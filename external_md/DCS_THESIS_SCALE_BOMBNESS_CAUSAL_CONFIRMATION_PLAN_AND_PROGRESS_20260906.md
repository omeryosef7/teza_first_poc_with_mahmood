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

## 2026-09-07 · Q-012 · a gap in my own preregistration, resolved from the artifact before the outcome

All three **button** banks are extracted and verified — 22,272/22,272, `failures: {}`,
`bank_rows_sha16` matching the pin, `eager`, `codeword_last` — in 58–59 min each. The three basket
banks are still running.

That made a gap in `PR-048` visible: **`primary.statistic` never names a codeword.** It says
*"3-way argmax accuracy on the 23 untouched TEST domains, domain-mean"* and stops. With half the
banks in hand, that ambiguity would have been resolved at analysis time, by me, knowing which
banks were available — which is exactly the shape of a post-hoc choice.

**Resolved now, from the frozen artifact rather than from preference.** The primary **pools both
codewords**, and the evidence is arithmetic:

- `power.deff_at_m60 = 6.22` and `power.n_eff_test_rows = 222` are computed at **m = 60** rows per
  domain;
- the bank carries **30** rows per domain per concept per codeword;
- so **m = 60 is two codewords**. The frozen power analysis already assumed pooling.

And `A-039` rule (4), adopted into this log before extraction, says it in terms: *"use both
codewords (SD 0.1514→0.1406, n_eff 193.6→222.0, and a free generalisation axis)."*

**This does not conflict with mandate §5.3.** That section forbids pooling button and basket into
training for the flagship **lexical-generalisation** claim — which is
`secondary.lexical_transfer`, and which is explicitly a **separate fit**: *"train on button TRAIN
domains, evaluate on basket at the SAME untouched TEST domain ids, no retraining."* Two fits, one
pooled for concept identity and one button-only for transfer, neither borrowing the other's
numbers.

**Consequence: the primary waits for all six banks.** Running it on the three finished button banks
would be a different estimand than the frozen one *and* a peek at TEST. Having spent this phase
building machinery specifically to prevent that, routing around it by hand because half the data
happens to be ready would be the worst kind of shortcut.

Recorded as `Q-012` and flagged for Omer: a preregistration whose primary statistic omits a
population axis is a defect in the preregistration, even when the axis is recoverable. The next one
states the codeword scope in the statistic line.

---

# 2026-09-07 · A-043 · FOUR-HOUR FULL REVIEW #2 (mandate §29)

Window `e4d78bf0..b5359329`. Three lenses. Reports:
`reports/DCS_TS_REVIEW2_{CODE,DATA,SCIENCE}.md`. It found **three CRITICALs in the analyzer, an
eighth instance of the compound class inside the C-087 fix, a seventh unfalsifiable check, and an
arithmetic error in my own Q-012 resolution.** Everything below is fixed or recorded; all of it was
found **before any outcome existed**, which is the only reason it was cheap.

## C-091 · **the frozen analyzer could never have run**

`LogisticRegression(multi_class="multinomial")` — the kwarg was **removed in scikit-learn 1.7**,
and **1.9.0 is installed**. Confirmed by execution:
`TypeError: LogisticRegression.__init__() got an unexpected keyword argument 'multi_class'`.
`run_probe()` would have died on the **first of 36 selection fits, after loading ~6 GB of
representations.** The file I committed as "the frozen analyzer, written before the outcome
exists" was, as committed, incapable of producing any outcome at all.

Amended, and **the amendment is not behaviour-neutral for `PR-049`**: with two classes the removed
kwarg forced softmax, whereas the default path is binary. For three classes sklearn 1.9's default
is softmax (verified: `coef_.shape == (3, n_features)`), so the primary is unaffected; the choice
is now recorded in the artifact rather than left to a default that changed under us.

## C-092 · **the null and the observed statistic were fit by different estimators**

The observed fit used `max_iter=2000`; the permutation fit used `max_iter=200`. **A permutation
test is valid only when the labels are the sole difference between the two pipelines.** The
permuted problem is strictly harder — 68 mutually inconsistent within-domain label maps — so if the
budget binds, it binds **on the null draws**, depressing null accuracies, reducing exceedances, and
making **p too small**. The reviewer timed it at the real shape and found convergence in 9–14
iterations, so it probably never bound; *probably* is not a property, and an artifact produced
under a binding budget would have been indistinguishable from a valid one.

Both paths now go through **one** `fit_score()` with one `MAX_ITER`, the permutation rebinding only
the labels, and **`ConvergenceWarning` is captured and persisted** rather than swallowed.

## C-093 · running the co-primary would have destroyed the primary

`--out` defaulted to a single fixed path and **both** preregistrations name this same analyzer.
Running `PR-049` would have overwritten `PR-048`'s result — while Holm needs both. Now derived from
the preregistration id.

## C-094 · the analyzer never checked that the extraction was COMPLETE

It verified bank sha, position and attention — **all three of which pass on a 4-row smoke run.**
`n_rows_captured`, `n_failed` and `knockout_applied` were never checked, so a partial extraction
would have been analysed as if it were the population. Now all three refuse.

## C-090 · the EIGHTH instance — inside the `C-087` fix, triplicated across three files

`has_compound()` compared the substring count against `\bconcept\w*\b` — which **matches a prefix
compound**. `gunfire` satisfies it, so the counts agreed and the check returned False, while
`str.replace` would produce `buttonfire`. Blind to exactly the direction the original defect did
not happen to take: `gunfire`, `bombardment`, `knifepoint` all passed.

Fixed to compare against standalone-word occurrences. Verified on all four prefix cases and three
legitimate ones. **Rescanned the shipped pools: 1 hit in 13,920 — the already-excluded
`subway_station` handgun.** The defect was **latent, not live**; the banks are unaffected.

## C-095 · the SEVENTH unfalsifiable check — my own mutation harness

`dcs_ts_verify_ts116n.py` printed *"4/4 RED — every gate must be demonstrably falsifiable"* while
carrying **no mutation for either gate added in this window** — neither the inflection/case check
(`C-076`/`C-079`) nor the compound check (`C-087`/`C-090`). A harness that does not attack a gate
cannot certify it, and printing a total that silently omits the untested gates is worse than
printing nothing.

Three mutations added — an extra inflected occurrence, an unenumerated case form, and a compound.
**All three go RED. 7/7 mutations now turn a gate RED**, and the total covers every gate.

## C-096 · my Q-012 arithmetic was wrong by 3×

I wrote that the bank carries *"30 rows per domain per concept per codeword"*. **It carries 10** —
30 is the all-query-kinds count, and the primary binds one kind. So `m=60` is 10 × 3 concepts × 2
codewords, which still resolves to **two codewords** and leaves the pooling conclusion unchanged.
The premise as written was wrong and is corrected rather than left for a reader checking the
arithmetic. Also fixed: exclusions were being selected by testing whether the prose `scope` string
*contains* `"ENTIRE"` — the `C-086` construction one window later, correct today only by luck of
wording. Now a required boolean `whole_population`, and an exclusion that fails to declare it is a
refusal.

## What the data lens could NOT break — including the check nobody had run

- **6/6 banks**: `bank_file_sha16` and `bank_rows_sha16` both recompute to the `PR-048` pins;
  0 duplicate `prompt_id` in 133,632 rows; flat 192 rows/domain.
- **3/3 completed extractions**: `DONE.json`, 22,272/22,272, `n_failed=0`, sha matching, `eager`,
  `codeword_last`, `knockout_applied=false`, and the **cache tensor count loaded and counted**
  rather than read off a summary field.
- **The representations themselves, checked for the first time**: 66,816 tensors all `(9, 4096)`,
  **0 NaN/Inf**, **0 of 22,271 equal to row 0**, norms rising monotonically 5.5→9.6 with sd
  0.26–0.50. An extraction that had silently captured one vector 22,272 times would have passed
  every earlier check.
- **The check that matters most, and it passes decisively.** For matched `prompt_id`, bomb-bank and
  knife-bank reps are **0/300 identical**, and TRAIN-only layer-9 cosine is **0.9006 bomb↔knife**
  against **0.9429 within-bank same-domain**. **The concept swap moves the representation FURTHER
  than the prompt swap**, at all nine layers. This is not `C-074`.
- Population binds **6,840 rows** (4,080/1,380/1,380), exactly the independent figure; split
  integrity holds at 68/23/23 over 114 domains.

## Recorded, not yet acted on

- **D2-05**: `restaurant_kitchen`'s exclusion rationale quotes a sentence from the **ts116n** pools,
  not the pinned `tsm` pools — and all 116 domains of the pinned pools are already clean
  (0/13,920 cross-concept). The exclusion is therefore **conservative rather than necessary** on the
  live corpus, as `C-082` already suspected. Kept; the rationale text is stale and is flagged here.
- **D2-07**: truncated sentences are **53 of 13,920**, not the 1 the preregistration names —
  104 of 6,840 primary rows, and in TEST that is bomb 10 / knife 0 / gun 4. An **asymmetric**
  nuisance that no gate currently measures. → new `Q-013`.
- **D2-04**: G2's rule text says 116/116, its recorded result says 115/115, and the verifier now
  computes 114 — three populations in one frozen file. The **bytes are stronger** than the record
  (the reviewer measured 116/116), but *"19/19 PASS"* is not reproducible from the file as written.
- **D2-01**: this log said "the three basket banks are still running". That is wrong: **one** job
  runs all four remaining banks sequentially. Finish ≈08:51 against a 10:44 wall — 1h53m margin,
  but **one node failure now costs three banks, not one.**

## 2026-09-07 · A-043 (science lens) · **the phase has no instrument that answers the register confound**

The hardest and most useful finding of the review, and it is a verdict about the phase rather than
about a script. Quoted in substance because softening it would be the whole failure mode:

> N5 was disqualified by `C-078`, rightly. `PR-047` — cited repeatedly in this log as the answer to
> localisation — **never existed**. `PR-049` survives its kill condition only because that
> condition was scoped to **hedges** while the confound is **register**: a broader surface
> classifier reaches **0.7065** on knife-vs-gun and **0.6870** with every length channel removed.
> That is **structurally the same defect `C-078` diagnosed in N5** — a bar answering a narrower
> question than the one being asked.
>
> Register has been converted from an unknown into a **quantified floor**, which is real progress.
> **But a floor is a bar, not an answer, and nothing applied even the bar.**

### C-097 · **`B-020` recurred inside the code written to fix `B-020`**

`dcs_ts_prereg.py` defines `require_gate()` and `require_null()`. **The analyzer never calls
either.** Eight nulls are declared in `nulls_required`; the analyzer implemented exactly **one**
(N2). And `primary.success` said only *"significantly above chance"* while the honest nuisance
floor sat elsewhere **in the same file, read by nothing**.

**A knife-vs-gun result of 0.60 would have PASSED the frozen success rule while sitting below a
17-feature bag of surface counts.** That is a published threshold no code path reads — the exact
failure `B-020` named — recurring *inside the file written to fix it*, by me, one window later.

**Fixed:** the floor is now a machine-read field in `primary.nuisance_floor` (**0.9217** for the
3-way, **0.7065** for knife-vs-gun), fetched through `require()` so a preregistration that forgets
to declare one **cannot be analysed at all**, and the analyzer now prints an explicit verdict:
`SUPPORTS THE CLAIM` / `SIGNIFICANT BUT BELOW THE NUISANCE FLOOR — NOT EVIDENCE FOR THE CLAIM` /
`NOT SIGNIFICANT`. **Amended before any outcome exists.**

### C-098 · **`PR-047` never existed, and no data was captured that could support it**

I cited the positional contrast in `C-078`, in `PR-049`'s rationale and repeatedly in this log as
the instrument that answers localisation. **It was never written.** Worse, all six extractions
capture `--position codeword_last` only, so **no hidden state existed at any control position** —
the instrument was not merely unwritten but unproducible from what I ran.

**Acted on immediately:** job **860778** queued at `--position last` over all six banks, and two
preregistrations written that should have existed before the extraction was designed.

### S-3 · `H_bind` and `H_gist` predict the same thing for the planned primary

"The codeword is represented as BOMB" and "the prompt is about bombs" make the **same prediction**
for `PR-048`. A probe at the codeword cannot separate them, because a gist representation is
available at the codeword too. The phase noticed the threat (`A-042`'s interference bank) and filed
it as post-probe future work. That was wrong: it is a **wording constraint on CLAIM A right now**.

## 2026-09-07 · PR-050 and PR-051 · the two missing instruments, both frozen before any outcome

**`PR-050` — surface-matched re-analysis. Answers REGISTER. Zero GPU.**
Fit the 17-feature surface classifier on TRAIN only, stratify TEST rows by its predicted-probability
vector, and re-run the frozen probe **within strata** where surface features are uninformative by
construction. Plus the cheapest discriminator available: the **per-domain correlation between probe
accuracy and surface accuracy** across the 23 test domains — one `pearsonr` over two existing
23-vectors. **Kill condition:** if no preregistered stratification drives the surface classifier to
chance with usable n, then register cannot be separated from concept on this corpus and the honest
verdict is **CANNOT ANSWER**, to be stated as such rather than absorbed by another instrument.

**`PR-051` — positional contrast. Answers GIST vs BINDING.**
The same frozen probe at `codeword_last` versus `last`, paired by domain. **The interpretation is
fixed before the numbers exist:** codeword ≫ control is consistent with binding; **codeword ≈
control is consistent with gist, and would mean CLAIM A must be narrowed to a decodability
statement about the prompt, not about the codeword**; control ≫ codeword means the read site is
wrong. Its nuisance floor is **0.0 by construction** — both sites see the *same* prompt, so every
surface confound is common to both and differences out. That is precisely why the paired contrast
is worth running: the confound that defeats the absolute measurement cancels in the difference.

Both carry blocking checklists, including that neither `PR-048`'s nor `PR-049`'s power transfers to
a within-stratum or paired estimator.

## The review's verdict on this phase's character, recorded because Omer has to defend it

Asked whether nine corrections in one window is evidence of rigour or of an untrustworthy pipeline,
the reviewer answered **rigour, with a checkable proof**: *nine of the ten corrections in this
window cost the phase something; the one that helped (`C-084`, the token-vs-character correction)
was found by an independent lens, not by the author.* A pipeline being talked up would show the
opposite ratio.

The honest caveats it attached, which I am not going to soften: **the find rate is not
decelerating** — `C-088` found three GREEN mutations *after* the harness-hardening commit — and
**every guard shares an author with the thing it guards.** That is the strongest available argument
for keeping independent adversarial lenses running rather than trusting the harnesses.

## 2026-09-07 · R-108 · 30 extraction failures, all one domain, and the guard was wrong

`basket_bomb` returned **22,242 / 22,272 with 30 failures** — the first extraction that is not
clean. Every failure reads `resolve:occurrence_count_mismatch: text=N, tokens=N+1`: **always
exactly one more TOKEN occurrence than TEXT occurrence.**

**Diagnosed, not assumed: all 30 are `school_campus`.** It is `C-075`'s `basketball` defect, and at
extraction it is not a metadata nuisance — `resolve_occurrences` found an extra token occurrence
and **refused rather than guessing which one was the codeword**. That is correct behaviour. 15 in
cell A, 15 in cell C; 3 of them in the primary population; the domain is in TRAIN.

**`school_campus` is therefore widened to a WHOLE-POPULATION exclusion** in all four
preregistrations. Its earlier scope — occurrence-ordinal analyses only — was written before we
knew the pipeline would refuse the rows outright. Validation and test are untouched; **the analysed
split becomes 67 / 23 / 23 over 113 domains.**

**And my `C-094` guard was the wrong guard.** A blanket `n_failed == 0` would have refused this
bank outright and told me nothing about why. The right rule is that every row missing from the
cache must belong to a **preregistered excluded domain** — an *explained* failure passes, a single
**unexplained** one refuses, naming the domains. That is strictly stronger than `n_failed == 0` on
a clean run, and it does not silently tolerate the case it was written for.

## 2026-09-07 · C-099 · the control site I queued was chat scaffold

`W3` verified `--position last` against all four criteria and it passes them all —
token-identical across concepts 2280/2280 triples, strictly after every codeword 6840/6840, no
concept surface, present 6840/6840. **And it is pure chat scaffold**: the token is `'\n\n'`
(id 271) in **6,840/6,840**, the terminator of the generation header, five tokens past the last
content token.

A scaffold control is a weaker instrument than a content one, and `PR-051`'s interpretation turns
on which it is. The token-role map's own nomination was **`rel_end = −9`, `' actually'`** — the
repo's `following` site, which `resolve_occurrences` has **always returned** and which the CLI
**never exposed**, so no run could capture it.

`--position following` added; job **860778 cancelled** while still pending (start estimated 12:59,
so nothing was lost) and replaced by **860873** capturing the content control. Same cost, better
instrument.

⚠ Also flagged and true: `PR-051`'s `artifacts.extraction` says "no additional forward passes"
while its own `design.sites` requires a control extraction. That is a contradiction inside a frozen
file, written by me, and it is corrected rather than argued away.

## 2026-09-07 · C-100 · **PR-050's central premise is false**

`Z1` tested 17 candidate stratifications, scoring 100 strata for the 3-way and 74 for
knife-vs-gun. **Zero usable strata reach chance on either contrast**, even under the weaker
CI-covers rule. Closest usable: 0.4609 (3-way) and 0.5826 (2-way).

`PR-050` asserts that within a surface-matched stratum the surface classifier is at chance **"by
construction"**. **It is not, and the reason is elementary: a partition cannot change pooled
accuracy** (0.5913 / 0.6630 under every stratification tried), and conditioning on the predicted
score does not balance the arms. Refitting inside the most favourable stratum still gives 0.4986 /
0.5609 — **binning removes confidence, not information.** I asserted a mathematical property that
is simply untrue, and the kill condition I attached is now the operative clause.

**One construction does work and is not preregistered:** arm-balanced joint simplex cells on
knife-vs-gun — surface accuracy **0.5054**, CI [0.4629, 0.5479], 552 rows (60 %), all 23 domains,
refit-within 0.5109. For the 3-way, **0 of 17** arm-balanced constructions work.

## 2026-09-07 · C-101 · **PR-049's published power was overstated, and it fails at its own Holm alpha**

`Z2` recomputed the variance components and reproduced `PR-048`'s icc / deff / n_eff to four
decimals — so the correction is a correction, not double counting. On that basis
**`PR-049`'s unstratified knife-vs-gun power is 0.905 / 0.793, not the published 0.963 / 0.900.**

**0.793 is below 0.80 at the Holm alpha `PR-049` itself declares**, before any stratification is
taken. `R-106` called it CO-PRIMARY on the strength of 0.900. That verdict is **withdrawn**: by the
demotion rule already written into `PR-049`, knife-vs-gun is **EXPLORATORY**, and the trigger is
not the SD>0.188 route I anticipated but a straightforward arithmetic correction to the power
itself. And within the one clean stratum `Z1` found, power is **0.721** — so the surface-matched
route is **not powered either** (MDE 0.1062–0.1186 against a +0.15 bar; roughly 0.06–0.09 of Holm
power lost per halving).

**Where this leaves the register question, stated plainly.** `PR-050` as frozen rests on a false
premise; the only stratification that achieves balance is unpreregistered, 2-way only, and
underpowered. **The register confound currently has no adequately powered instrument.** That is a
**CANNOT ANSWER** unless something changes, and per `PR-050`'s own kill condition it will be
reported as one rather than absorbed by the positional contrast.

## 2026-09-07 · PR-050 WITHDRAWN · PR-052 written EXPLORATORY · and the structural conclusion behind both

**`PR-050` is WITHDRAWN, not amended.** Its central premise is false (`C-100`), and amending a
false premise into a different design *is* a new design — mandate §21 says that gets a new
preregistration. The file stays byte-frozen as the record of a design that did not survive its own
first check. The loader now refuses it on `status != FROZEN`, which is the behaviour I want.

**`PR-052`** carries the one construction that does work — arm-balanced joint simplex cells on
knife-vs-gun, surface accuracy **0.5054** CI [0.4629, 0.5479] over 552 rows and all 23 test
domains — and is **declared EXPLORATORY before it is run, not after it disappoints.** `Z2` measured
conjunctive power there at **0.721** under Holm, against an MDE of 0.1062–0.1186 for a +0.15 bar.
Mandate §20 forbids running a confirmatory experiment whose likely negative would be
uninterpretable, so `success` and `negative` are both marked **NOT AVAILABLE** in the file itself:
it can produce a point estimate with an honest interval where surface information is *verifiably*
absent, and nothing more. Its nuisance floor is the **measured** 0.5054, not the nominal 0.5.

### The structural conclusion, which matters more than either file

Three instruments have now failed to answer the register confound, and they failed for the **same
underlying reason** rather than three unrelated ones:

| instrument | why it failed |
|---|---|
| **N5** (text baseline) | reads the *treatment*; no representation probe can beat it (`C-078`) |
| **PR-049** (knife-vs-gun) | register is only *partly* smaller there — surface reaches 0.7065 (`R-106`) — and it is underpowered at its own alpha (`C-101`) |
| **PR-050** (surface matching) | a partition cannot remove information; balance costs the power needed to use it (`C-100`, `Z2`) |

**The common cause: register is not a nuisance layered on top of the manipulation — it is
*produced by* the manipulation.** We asked a generator for naturally concept-specific
demonstrations, and natural bomb text hedges while natural knife text does not. Every
analysis-side remedy either reads the treatment, or conditions on it and destroys the power, or
narrows the contrast until register shrinks and n shrinks with it.

**No re-analysis of this corpus can fix it.** The fix is a *design* fix, and it belongs to the next
data build: generate the harm pools under an explicit **register constraint** — matched hedge
rate, matched threat-lexicon density, matched sentence structure — so the arms differ in concept
affordance and in nothing else. That is expensive (a new generation campaign with per-sentence
constraints and a much stricter accept filter) and it is the only thing on the table that would
turn register from a **stated limit** into a **controlled variable**.

**So the honest position for this phase, recorded before the primary is computed:** register is a
**stated scope limit**, the probe result will be reported **against a measured surface floor rather
than against chance**, and the register question itself is **CANNOT ANSWER on this corpus** — with
a concrete, costed recommendation for what would answer it. That is a more useful thing to hand
Matan than a confirmatory number that quietly rests on a confound.

→ **`Q-014` for Omer:** fund a register-matched regeneration for the next phase, or accept register
as a permanent stated limit of this bank family? The measurement that decides it already exists
(`R-106`: hedge 13.72 / 0.20 / 2.33 %, surface 0.7065 on the cleanest contrast).

## 2026-09-07 · C-102 · fair-share ran out, and the fix was fewer rows rather than different hardware

The `PR-051` control extraction was estimated by SLURM to start at **2026-09-10 01:03 — three days
out.** Fair-share is depleted after today's GPU hours; this is the priority wall, not a capacity
wall.

**The tempting fix was the wrong one.** The house note says to fall back to a5000/3090 in
`killable` when L40S is full, and those cards do support bfloat16 — we use *eager* attention, so
the usual flash-attention objection does not apply. **But `PR-051` is a PAIRED contrast between two
read sites.** Extracting the control on different hardware would confound bf16 matmul numerics
**with the very thing being tested**. Same hardware, or the contrast is worthless. Rejected.

**The right fix: extract only the rows the analysis reads.** `PR-051` needs the analysis population
— cell C × `semantic_one_word` × `n_examples=4` — which is **1,140 of 22,272 rows per bank, a 20×
reduction**. The other 21,132 rows per bank would have cost ~6 GPU-hours to produce for no analysis
that reads them.

Added `--only-cell` / `--only-query-kind` / `--only-n-examples` to the extractor (refusing loudly
if the filter selects **zero** rows, so an empty extraction cannot masquerade as a completed one)
and plumbed them through the multi-bank driver. Job **860873 cancelled**, replaced by **860925**
with a **1.5 h** limit — short enough that SLURM's **backfill** can place it in a gap, which a
six-hour job cannot occupy.

This is a scheduling change, not a scientific one: the control is captured at the same read
convention, on the same hardware class, from the same pinned banks, over exactly the rows the
paired contrast compares.

## 2026-09-07 · a dress rehearsal for the analyzer, before the run that matters

`--stop-after-selection` added: it binds the population, verifies every bank hash, loads the
caches, fits all 36 selection points on **validation**, prints the `SELECTION_TRACE` — and
**stops without touching TEST.**

`run_probe()` has never executed end to end on real representations, and `C-091` showed the frozen
file could not even construct its estimator. The first real run — the one that reads the test split
once — is not the place to discover a runtime error. The dry run exercises everything except the
irreversible step.

## 2026-09-07 · R-109 · **all twelve extractions complete and verified, at both read sites**

| family | banks | cached | attempted | missing | unexplained | sha | position |
|---|---|---|---|---|---|---|---|
| `ts116m_full` (primary) | 6/6 | 22,272 ×3, 22,242 ×3 | 22,272 | 0 ×3, **30 ×3** | **none** | all OK | `codeword_last` |
| `ts116m_following` (control) | 6/6 | 1,160 ×3, 1,157 ×3 | 1,160 | 0 ×3, **3 ×3** | **none** | all OK | `following` |

**Every missing row is explained by the `school_campus` exclusion, and the pattern is exactly what
`R-108` predicted:** 30 per *basket* bank at the full population and 3 per basket bank in the
analysis population, **zero in every button bank** — because `basket` collides with `basketball`
and `button` collides with nothing. A defect that reproduces its own predicted arithmetic in a
second, independently-scoped extraction is a defect that is understood.

Job 860468 `COMPLETED 0:0` in 4:09:45; job 860925 in **29:10** — the 20× row reduction turned a
job SLURM would not start for three days into one that **backfilled within minutes**.

**`PR-051`'s W1 and W3 are closed**, and its control site is corrected in the frozen file from
`last` to **`following`** (`rel_end −9`, `' actually'`, id 3604), with the reason recorded: `last`
passes all four formal criteria but is the generation-header terminator `'\n\n'` in 6,840/6,840
prompts — pure chat scaffold. Its `artifacts.extraction` claim of *"no additional forward passes"*
is also corrected: a second read site necessarily requires a second forward pass, and saying
otherwise was simply wrong.

## 2026-09-07 · C-103 · the dress rehearsal paid for itself on its first run

`--stop-after-selection` failed immediately:

> `basket_bomb: captured 22242 of 22272 bank rows -- PARTIAL EXTRACTION`

**A blanket `n_rows_captured == bank_n_rows` check that I failed to remove when I replaced the
failure guard.** It was written before `school_campus` became a whole-population exclusion, and it
vetoed all three basket banks — which are missing exactly the 30 rows the pipeline was **right** to
refuse. The blunt check was overriding the precise one sitting directly beneath it.

Removed, not weakened: the per-domain missing-row check is **strictly stronger** — it refuses any
missing row whose domain is not excluded, and an empty cache fails it because every domain would
then be unexplained.

**This is precisely what the rehearsal exists for.** Without it, the discovery would have happened
on the run that reads the test split — and the temptation at that moment, with the population
loaded and the answer one line away, is to reach for the quickest thing that makes the error go
away. Finding it in a mode that provably cannot read TEST removes that temptation entirely.

## 2026-09-07 · PR-053 · PHASE 6, difference-in-means, preregistered

Mandate §9 says in terms: *"Matan explicitly did not want us to abandon difference-in-means. Do
not."* The phase had spent its effort on the linear probe and had not started this. `PR-053` closes
it, at **zero additional GPU** — cells A and C were both captured in the `PR-048` extraction, at the
same read site, from the same pinned banks.

**Why the aligned bank matters more here than anywhere else.** The old estimate was confounded
because each concept had its **own** cell-A baseline, so `v_c` was a difference between two
independently generated corpora. On `ts116m`, cell A is **byte-identical across concepts** (gate
G3a, 3,680/3,680) — the A term is literally the same prompts in all three arms and **cancels
exactly.** That is the single cleanest thing this rebuild bought, and diff-in-means is where it
shows.

**The estimator has no hyperparameter at all.** No layer selection, no regularisation constant,
every layer 6–14 reported and none picked. That is its chief virtue over the probe: with nothing to
select, the `C-070` saturated-selection failure and the test-selection FPR inflation (0.4433 vs
0.0467) are both **structurally impossible** rather than merely avoided.

**The separability claim needs two results, not one.** Questions C *and* D from mandate §9.1:
`v_bomb_specific` must discriminate **identity** *and* stay **weak on generic remapping**. A
direction that does both equally well is not a separate axis — it is one axis doing two jobs.
Reporting C without D is exactly the error the raw-vs-residual framing exists to avoid, and the
preregistration says so explicitly so it cannot be quietly dropped later.

**Multiplicity updated before any outcome exists.** The PRIMARY family is now `PR-048` + `PR-053`
under Holm; `PR-049` has left it (demoted by `C-101`) and sits in an EXPLORATORY family alongside
`PR-052`, which carries no confirmatory weight. Two blocking items: **V1** power for an AUROC
estimator at n=23 (neither existing power analysis transfers), and **V2** verification that cell A
really is byte-identical in the *analysed* population — if it is not, the estimator does not work
and saying so is the deliverable.

The implementation must **reuse** `dcs_diffmeans_directions.py` rather than reimplement it, and
must **fix rather than inherit** its known `D1` defect, where `transfer()` leaks the held-out
domain into the standardisation constants.

## 2026-09-07 · R-110 · the dress rehearsal PASSES, and the selection is not degenerate

```
SELECTION (validation only): layer=9  C=0.01  best_val_acc=0.9138  n_tied=1/36  inert=False
--stop-after-selection: TEST WAS NOT READ.
```

**`n_tied = 1/36`, `inert = False`.** Against `C-070`, where the surface was `1.000000` at all 36
grid points and every pick was a grid-order tie-break reported for months as learned localisation,
this selection **actually selected something** — a unique optimum at layer 9. It is the first
non-degenerate layer selection in this project's recorded history, and it is recorded here with
its trace rather than as an adjective.

⚠ **One thing visible on VALIDATION, stated now rather than after the test read.** Validation
accuracy is **0.9138** and the preregistered nuisance floor is **0.9217**. Validation is not test,
and nothing is concluded from it — but it is the honest early signal that the probe may land **at
or below** the surface floor. That is precisely the outcome `C-078` argued was likely, and the
reason the floor was pinned into the config and made machine-read *before* any of this was
visible.

## 2026-09-07 · C-104 · the permutation was a ~140-hour job, and the rehearsal is why that is not a crisis

36 selection fits took 31 minutes. Extrapolated, 10,000 permutation draws is **~140 hours** — and
meeting that number mid-run, with the test split loaded and the answer one line away, the pressure
to cut `n_perm` back toward the arithmetic floor `C-069` exists to prevent would have been
considerable.

**Measured instead of extrapolated.** A single fit at the **selected** config is **2.8 s**
(14 lbfgs iterations). The 36 were slow because the weaker-regularisation configs converge slowly;
the one config the permutation actually uses is fast. True cost: ~7.8 h of fitting, **plus ~3.4 h
of redundant `StandardScaler` refits** inside the draw loop.

Two speedups, both **provably label-independent**, so the `C-092` invariant holds — the null and
the observed statistic stay identical in everything except the labels:

1. **the scaler is fit once.** It depends on the features and the fixed train mask, never on `y`,
   so it cannot differ between draws;
2. **the draws are parallelised** — they are embarrassingly parallel by construction.

**`n_perm` is NOT reduced.** Making the null cheaper than the observed statistic, or shrinking it
until `p` returns to its floor, are both refused — and the refusal is written into the code comment
so the next person to meet a slow run sees the reasoning rather than just the constant.

**This is the third defect the rehearsal has caught** — after the blunt completeness check
(`C-103`) and, at construction time, the estimator that could not be built (`C-091`). The pattern
worth keeping: a mode that provably cannot read TEST removes the temptation that makes mid-run
fixes dangerous.

## 2026-09-07 · C-105 · the rehearsal cannot test the code I just changed

`--stop-after-selection` stops **before** the permutation. So the dress rehearsal — the thing built
specifically to de-risk the run that reads TEST — **cannot validate the permutation path at all**,
and the only other thing that exercises it is the irreversible run itself. That asymmetry is
precisely how an untested code path reaches a step that cannot be taken back, and I nearly let the
rerun stand in for a test it structurally cannot perform.

Tested synthetically instead, on a construction with **no signal**, asserting two properties:

| property | why it matters | result |
|---|---|---|
| the null centres on chance under pure noise | a null that does not is measuring something other than "labels shuffled" | **PASS** |
| within-domain permutation preserves the class marginals **exactly** | if it did not, the null would be testing a *different design* than the observed statistic — the `C-092` failure in another guise | **PASS** |
| the parallelised path returns one statistic per draw | the speedup must not silently drop or duplicate draws | **PASS** |

**16/16 guards reachable.** Also noted: run under the bare `python3` the new test reports
`ModuleNotFoundError: numpy` as a **FAIL** rather than crashing the suite — which is the right
behaviour, since a guard that cannot run is not a guard that passed.

## 2026-09-07 · the confirmatory analysis goes to SLURM, not the login node

`src/boombness/slurm/run_ts_analysis_cpu.sh`. CPU-only — the representations already exist, and
taking a GPU slot for a scikit-learn job would be waste in a queue where fair-share is already
spent (`C-102`).

Mandate §26.17 forbids long inference on the login node, and the practical reason bites here: this
is ~1.5 h of saturated multi-core work, and **a login-node run that gets killed halfway is a run
whose test split has been read for nothing.** There is no second first read.

`OMP_NUM_THREADS` is **pinned to 1**, with parallelism taken at the joblib level instead. Leaving
BLAS free to choose a thread count makes the numerics depend on how busy the node happened to be,
so two runs of the same frozen analyzer could disagree in the last digits — and this project
already records `OMP_NUM_THREADS` as a binding reproduction constant elsewhere (`A-031`). One place
to reason about, and it is the place the speedup actually comes from.

## 2026-09-07 · C-106 · two preregistrations disagreed about the Holm family

The pre-submission checklist printed the primary family and it read **one member**. `PR-053`
declares **two**. Holm is defined *over a family* — two configs disagreeing about which hypotheses
are in it means the correction is **undefined**, and whichever file the analyzer happened to read
would silently set the threshold.

Caught by printing the family as part of a manual checklist, **not by any guard** — none of the
sixteen looks across preregistrations. One identical `multiplicity` block is now written into all
five, and verified byte-identical by hashing it in each file (`31589eb781be` in all five).

Final family, fixed before any outcome exists:

| family | members | correction |
|---|---|---|
| **PRIMARY** | `PR-048` 3-way accuracy · `PR-053` `v_bomb_specific` AUROC | Holm, α=0.05 family-wise |
| SECONDARY | AUROC variants, lexical transfer, n_ex=8 replication, hedge-free stratum, mandate §9.1 A–F, per-layer profile, `PR-051` | Holm within family |
| EXPLORATORY | `PR-049` (demoted, `C-101`) · `PR-052` | none — no confirmatory weight |
| NULLS N1–N8 | diagnostics | not corrected; gates, not hypotheses |

An absent member enters Holm at **p = 1.0** rather than being dropped.

## 2026-09-07 · **THE PRIMARY IS SUBMITTED — job 861367, the first and only read of the test split**

Everything that gates it, verified immediately before submission:

| check | result |
|---|---|
| preregistration gate, `for_extraction` | clean — FROZEN, **17 hashes verified against disk**, all 12 mandate-§21 fields |
| analyzer guards | **16/16 reachable** |
| frozen bank gates on `ts116m` | **19/19 pass** |
| split manifest | 6/6 checks, `manifest_sha16 be7d2c772d814ef3` |
| dress rehearsal | passed **twice, bit-identically**: layer 9, C=0.01, val 0.9138, `n_tied=1/36`, `inert=False` |
| permutation path | synthetically validated — null centres on chance, marginals exact, one statistic per draw |
| Holm family | byte-identical across five preregistrations |

`PR-049`'s demotion contingency is moot: `C-101` already demoted it to EXPLORATORY by a
straightforward power correction (0.793 against its own Holm α), so the SD>0.188 route never
needed to fire.

**What the run will report, and the shape of the answer is already fixed.** Domain-mean 3-way
accuracy over 23 untouched test domains, against **chance 1/3 and the measured nuisance floor
0.9217**, with a domain-level group permutation at `n_perm=10000` and every p printed beside its
floor. The analyzer emits one of three verdicts and cannot emit anything else:

- `SUPPORTS THE CLAIM`
- `SIGNIFICANT BUT BELOW THE NUISANCE FLOOR — NOT EVIDENCE FOR THE CLAIM`
- `NOT SIGNIFICANT`

**Validation accuracy was 0.9138 against a 0.9217 floor.** The middle verdict is a live
possibility, and it was made a printable outcome *before* that was visible — which is the only
reason it will be believable if it prints.

---

# 2026-09-07 · R-111 · PHASE 6 RESULT · **CLAIM B is UNSUPPORTED**, and the check that found it was preregistered for exactly this

`scripts/dcs_ts_pr053_diffmeans.py`, `reports/DCS_TS_PR053_DIFFMEANS.md`. Analyzer selftest 12/12;
mutation harness **9/9 RED, 13/13 cases as declared** (4 GREEN-by-design controls), including
sha-pin corruption, missing rows outside the exclusions, a byte-flipped cell-A prompt turning V2
red, the `A-039` wrong-field zero-bind, and fitting directions on the evaluation domains. The `D1`
leak in `dcs_diffmeans_directions.py` is **fixed here, not inherited**, and that file was not
edited.

## The gates

**V2 PASSES, 3,616/3,616** — cell A is byte-identical across the three concepts at matched
`prompt_id` in all six codeword×dose cells. And the numerical corollary is the one I actually
wanted: at matched `prompt_id`, cell-A hidden states from **three separate extraction runs** agree
to `max|diff| = 0.000e+00`. **The A term cancels in arithmetic, not merely in text.** That is the
whole payoff of the aligned rebuild, measured rather than argued.

**V1 PASSES** — realised between-domain SD **0.0347**, MDE 0.0203, far below the 0.2479 needed to
clear the measured surface floor. Adequately powered at every point of the assumed bracket.

## The primary

**`v_bomb_specific`, C_bomb vs {C_knife, C_gun}, band-mean L6–14, domain-mean over 23 untouched
test domains = 0.9764**, CI [0.9622, 0.9906], d = 3.03, **23/23 domains**, clearing the measured
surface floor of 0.7479 by **0.2285**.

Permutation **p = 0.0454** [floor 9.999e-05, **453/10,000 exceedances**]. The sign-test p
(2.384e-07) **is** its own floor and is reported as such, not as a measurement.

## THE FINDING — and it is a negative

> **C is strong. D is not weak. CLAIM B is UNSUPPORTED.**

`v_bomb_specific` was supposed to read *identity* and stay quiet on *remapping*. It does not:

| mandate §9.1 question | result |
|---|---|
| **C** — does `v_bomb_specific` separate C_bomb from the hard negatives? | **0.9764** ✔ |
| **D** — does it stay **weak** on generic C-vs-A remapping? | **NO**: 0.8309 polarity-free on C_knife/C_gun vs A (21/23 domains), and **0.8236** on C_bomb vs A |

Both clear the surface floor. **The residual axis carries remapping and identity together —
residualising changed the mixture, it did not decompose it.** Replicates at both doses, both
codewords, validation and test.

**This is precisely why `PR-053` was written to require C *and* D.** Reporting C alone would have
produced the sentence *"a concept-identity axis exists, AUROC 0.976, 23/23 domains"* — which is
false, and which I would have had no way to catch after the fact. The preregistration says in
terms that *"a direction that discriminates identity AND remapping equally well is not a separate
axis — it is one axis doing two jobs."* It is one axis doing two jobs.

## A correction to inherited work, in the opposite direction

**B = 0.8856, reversing the old ~0.574.** The raw `v_bomb` axis **does** read concept identity —
once the A term genuinely cancels. The old finding that it did not was an artifact of each concept
having its own unaligned baseline. `A = 0.9969` (the remapping axis, near ceiling).
**E**: button→basket transfer **0.9747**, Spearman ρ = 0.9921 on per-domain ranks.
**F**: the n_ex=0 null fires exactly — ‖v‖ = 0.0, all contrasts exactly 0.5000, and flagged
degenerate-by-construction per `C-081`.

## Two methodological caveats that must travel with the number

1. **The concept-relabelling null is only properly centred for the residual family.** C's null mean
   is 0.4943 and D's is 0.5065 — but for the raw `v_bomb` family it is structurally off-centre
   (A's null mean 0.8794, B's 0.2230), because `mean_j w_j = 0` exactly while `mean_j u_j` is the
   grand remapping direction. **A's and B's permutation p-values are therefore not calibrated and
   are not quoted as evidence.** The point estimates stand; their p-values do not.
2. **The primary's null is BIMODAL**, sd 0.409: **4.5 % of arbitrary relabellings reach 0.9764.**
   So the effect is enormous *and* the label-permutation evidence that it is specifically **bomb**
   is thin — which is exactly why p = 0.0454 sits beside an AUROC of 0.9764. Reporting the AUROC
   without that sentence would badly overstate the case.

**Holm cannot be completed yet**: `PR-048` is still running (job 861367). The primary's confirmatory
status is contingent — **it rejects only if `PR-048`'s p is below 0.0454.**

## 2026-09-07 · C-107 · I nearly walled the run that reads TEST, with a fix of my own making

Job 861367 sat **57 minutes without emitting the selection line.** The cause was mine: pinning
`OMP_NUM_THREADS=1` — done so the numerics could not depend on how busy the node was — made every
one of the 36 **sequential** selection fits single-threaded. Only the permutation had been
parallelised. Measured multi-threaded that loop took 31 minutes; at one thread it is several times
that, and with a parallel permutation behind it the job was on course to approach its 6-hour wall.

**That is the exact failure this phase had already named in writing**, one tick earlier, when
justifying why the analysis goes to SLURM at all: *a run killed part-way is a run whose test split
was read for nothing, and there is no second first read.*

**Cancelled while still in selection.** The absence of the selection line is what proves TEST had
not been touched — the analyzer prints it immediately before the test read, so its absence is a
positive guarantee rather than an assumption. Selection depends on labels but not on the
permutation, and each grid point is independent of every other, so parallelising across grid points
changes *what is computed* not at all.

⚠ **But it does change the digits, and that must be recorded.** Re-running the rehearsal after the
change gives **`best_val_acc = 0.9130`** against the previous **`0.9138`** — same layer 9, same
C=0.01, same `n_tied=1/36`, same `inert=False`. The **selection is robust**; the fourth decimal is
not, because floating-point summation order differs between BLAS-threaded and joblib-parallel
execution. Pinning `OMP=1` was meant to remove exactly this dependence, and parallelising
reintroduced it one level up. **The layer/C choice reproduces; the accuracy value is not
bit-reproducible across parallelisation modes**, and any future comparison must be made under the
same mode.

Resubmitted as job **862952**.

---

# 2026-09-07 · R-112 · PHASE-51 RESULT · **GIST, not binding. CLAIM A must be narrowed.**

`scripts/dcs_ts_pr051_positional.py`, `reports/DCS_TS_PR051_POSITIONAL.md`.
**18/18 checks PASS, 14/14 mutations RED.**

## W2, the blocking gate — adequately powered, and the branch that refuses was in the code

Neither `PR-048`'s nor `PR-049`'s power transfers: both size an **absolute** accuracy, while this
is a **paired difference against 0.0**, a different variance component. Two arms at between-domain
SD 0.1406 admit a paired SD anywhere in ~0–0.199, so it had to be measured.

Measured on **validation only**: paired SD **0.0494**, below the `DEMOTION_CONTINGENCY` ceilings the
script **parses out of the frozen config and enforces**. Conjunctive MDE **0.0395**, power ≈1.000 at
the declared δ=0.15. A **derived** floor was added rather than assumed: at m=40 rows/domain/site the
paired SD cannot fall below `sqrt(2p(1-p)/m) = 0.1118` even with zero between-domain variance. The
underpowered branch — return without reading test — **exists in the code, not only in the prose.**

## The contrast

Both sites bound to **identical row sets**: 4,520 rows, 113 domains, 67/23/23, keyed on
`(bank, prompt_id)` and element-wise row-aligned — keying on `prompt_id` alone would have compared
1,130 keys where 4,520 rows exist, because the banks reuse ids. 12 absent rows, **0 unexplained**.

| | |
|---|---|
| codeword_last (primary site) | **0.9446** |
| `following` (control, 9 tokens downstream, token-identical across concepts) | **0.9261** |
| paired difference | **+0.0185**, CI (t) [+0.0042, +0.0328], bootstrap [+0.0054, +0.0326] |
| permutation, site-label sign flip, domain level | **p = 0.0157** [floor 9.999e-05, 156 exceedances — not at the floor] |
| sign test, 9 of 23 domains are **exact ties** | k⁺=12, k⁻=2, **p = 0.0129** [floor 1.221e-04] |
| nuisance floor for a paired difference | **0.0**, cleared |
| SELECTION_TRACE, both sites | primary L9/C0.01, control L10/C0.01; `n_tied=1/36`, **inert=False, saturated=False** — no `C-070` tie-break at either site |

## The verdict, and it is the unwelcome branch

Uncorrected, the difference is significant → *codeword ≫ control*. **Under the preregistered Holm
within the SECONDARY family** (8 members, first step α/8 = 0.00625) **both p-values fail** →
**`codeword ≈ control` → GIST.**

Both branches are reported; the uncorrected one is not withdrawn. But three things beyond the
correction point the same way:

1. the observed effect is **under half the conjunctive MDE** of a design with power ≈1.000 at its
   own declared δ;
2. it closes only **25 %** of the headroom left by a control that **already decodes identity at
   0.9261**;
3. that control sits **nine tokens downstream, token-identical across concepts, carrying no concept
   token** — and it still decodes concept identity almost as well as the codeword does.

> **CLAIM A must be narrowed to a decodability statement about the PROMPT, not about the codeword.**
> The concept is decodable from the residual stream at this depth; it is **not** meaningfully more
> decodable *at the codeword* than nine tokens later. On this evidence the codeword position is not
> special.

**This is the answer to the question the phase was built to ask**, and it is not the answer the
phase was hoping for. It was obtained from a contrast whose nuisance floor is **0.0 by
construction** — both sites see the *same prompt*, so register, length and every TF-IDF-recoverable
confound is common to both arms and **differences out**. The confound that defeats every absolute
measurement in this phase **cancels here**, which makes this the cleanest instrument the phase
owns — and it says gist.

## 2026-09-07 · A-044 · the pre-commit guard REFUSED a commit, and it was right to

`[pre-commit] REFUSING: a guard TEST failed -- a guard may no longer be able to fail.`
`tests/test_rah_preflight_spans.py::test_d11_provenance_block_is_emitted_and_complete`,
1 failed / 340 passed.

**Diagnosed rather than bypassed**, because a refused commit is the one moment where "just get it
in" is most tempting and least defensible.

The test **passes in isolation** and passes on demand right now. The mechanism is in
`rah_preflight_transport.provenance()`: `git_dirty` is a **deliberate tri-state** —
`bool(status) if ok_status else None` — and its own docstring says the `None` is on purpose,
because `RAH2-C-030` records that returning `None` on failure *and* on empty output once made
`bool(None)` report a **clean tree whenever git could not run at all**. The `_git` helper gives up
after a **20-second timeout**.

Measured here: `git status --porcelain` takes **5.2–5.4 s** in this working tree, against 25
untracked paths including the deliberately-untracked bank files. Under the pre-commit hook — which
is itself running git, holding the index, and competing with a 340-test suite on an NFS repo — 20 s
is reachable. When it is reached, `git_dirty` becomes `None` and the test's
`assert isinstance(p["git_dirty"], bool)` fails.

**So the test contradicts the design it guards.** It forbids exactly the "could not tell" state
that `RAH2-C-030` introduced on purpose. That is a real latent defect in the guard, not in my
change — and it is **not mine to fix**: `RAH2` is another phase's work, its author reasoned
explicitly about this tri-state, and silently tightening or loosening someone else's guard while
trying to land my own commit is precisely the move this project keeps recording corrections for.
**Recorded and left alone**, with the mechanism and the measurement, for whoever owns `RAH2`.

⚠ **My working tree makes it more likely.** The untracked `ts116`/`ts116m` bank files are what slow
`git status`. That is a cost of the decision not to commit 420 MB of regenerable rows, and it is
worth stating alongside the benefit.

**The stale lock.** The refused commit left a **0-byte `.git/index.lock`**. The standing rule in
this shared tree is that deleting a lock is destructive — but that rule is about a *third writer's*
in-flight commit. This one is mine, zero bytes, from a commit that had already been refused, and
**no `git` process was live** (verified by process listing before touching it). Removed under that
explicit check, not on assumption, and the staged file set was confirmed intact afterwards.

---

# 2026-09-07 · R-113 · **THE PRIMARY. Job 862952. The test split has now been read, once.**

```
rows=6780  domains=113  test_domains=23
SELECTION (validation only): layer=9  C=0.01  best_val_acc=0.9130  n_tied=1/36  inert=False
OBSERVED domain-mean accuracy = 0.9399   (chance 0.3333)
sign test    k=23/23   p = 2.38419e-07 [floor 2.384e-07]  <-- AT THE FLOOR, not a measurement
permutation  p < 9.999e-05 (FLOOR; 0 exceedances -- the design cannot resolve below this)
NUISANCE FLOOR 0.9217  ->  observed 0.9399  ->  clears_floor = True
VERDICT: SUPPORTS THE CLAIM
```

**Holm across the PRIMARY family, computed rather than asserted:**

| step | hypothesis | p | threshold | outcome |
|---|---|---|---|---|
| 1 | `PR-048` 3-way accuracy | < 9.999e-05 | α/2 = 0.025 | **REJECT** |
| 2 | `PR-053` `v_bomb_specific` AUROC | 0.0454 | α/1 = 0.05 | **REJECT** |

Both primaries reject. **And that is the least interesting sentence in this entry.**

## What must be said in the same breath

**1. The margin over the surface floor is 0.0182.** The probe reaches 0.9399; a **bag of words over
the demonstration block** reaches 0.9217. Clearing it by 1.8 accuracy points is a real result and a
narrow one, and the floor is a **point estimate with no interval** — I am comparing a point to a
point. The claim is "above the surface baseline", not "far above" it.

**2. Both p-values are AT their floors, and the analyzer says so in its own output.** `k = 23/23`
exhausts the sign test; 0 exceedances in 10,000 exhausts the permutation. These are statements that
**the design cannot resolve further**, not measurements of how extreme the effect is. That is
precisely the `C-069` failure — a headline p that *was* its own floor, read for months as a
measurement — and the reason every p in this phase prints beside its floor.

**3. Test (0.9399) came in ABOVE validation (0.9130).** Recorded because it is mildly unusual and I
would rather flag it than have a reader notice it. It is consistent with 23 test domains being an
easier draw than 23 validation domains; it is not evidence of anything and no weight is put on it.

**4. `PR-051` already established that this is NOT localised at the codeword.** A control **nine
tokens downstream**, token-identical across concepts and carrying no concept token, decodes the
same labels at **0.9261**. So 0.9399 is a fact about **what is decodable from the prompt at this
depth**, not about the codeword position being special.

**5. `PR-053` established that the residual axis does not separate remapping from identity.**
`CLAIM B` remains **unsupported** whatever its p-value does under Holm — a p-value cannot rescue a
design whose question D failed.

## The synthesis, stated as it would be to Matan

> On a 113-domain aligned population where only the harmful demonstrations differ, the installed
> concept is **linearly decodable from the model's residual stream at layer 9**, at 0.9399
> domain-mean accuracy over 23 untouched test domains, 23/23 domains above chance — **and above a
> concept-masked bag-of-words baseline, by 1.8 points.**
>
> It is **not** meaningfully more decodable at the codeword than nine tokens downstream, so this is
> a statement about the **prompt**, not about the codeword being "represented as BOMB".
>
> The remapping and identity axes are **not** separable by residualisation: the residual direction
> carries both.
>
> Whether any of this is **causally used** by the model is **untested** — no intervention has been
> run — and the **register confound has no adequately powered instrument on this corpus**, which is
> a CANNOT ANSWER with a costed fix for the next data build.

That is a narrower set of claims than the phase set out to make, and every narrowing came from an
instrument built in advance to be able to say so.

## 2026-09-07 · A-045 · `C-068`, `C-070` and the §13 ceiling are ONE fact, not three — and it explains why this phase's selection is healthy

The stood-down peer session sent a synthesis of its own handoff, unprompted, correcting itself.
Recorded here because it is right, because it is better than what it replaced, and because I
**verified its premise independently from my own bank** rather than taking it on trust.

**The premise, checked against raw rows of `ts116m_button_bomb`:**

| cell | rows | contain the concept word | **`target_surface == target_semantic`** |
|---|---|---|---|
| A | 5,568 | 1,856 | **0** |
| **B** | 5,568 | **5,568** | **5,568** |
| **C** | 5,568 | 1,856 | **0** |
| E | 5,568 | 5,568 | 5,568 |

Cell B: `target_surface='bomb'`, `target_semantic='bomb'` — **the capture token IS the concept
word, in 5,568 of 5,568 rows.**
Cell C: `target_surface='button'`, `target_semantic='bomb'` — the capture token is the codeword,
and the concept is what it *stands for*.

**So a probe at the capture site in cell B is reading the token `bomb` itself.** It cannot do
otherwise, and it must saturate. The mechanism is visible in one metadata field.

**The chain is then deterministic, not coincidental:**

> cell-B capture site **is** the concept word
> → any probe there saturates at 1.0000 (the §13 ceiling)
> → the selection surface is 1.000000 at all 36 grid points (`C-070`)
> → `select()`'s strict `>` has no maximum and returns the **first** grid element
> → the pick is **(6, 0.01)** in every fold of every cell-B-selected instrument
> → **L=6 is the first layer of the 6–14 knockout band**
> → at the band's first layer the two knockout scopes are provably identical at the read row
>   (0 differing fp16 bit patterns, 2,520 rows, 3 banks)
> → **gate R6 is uninformative by construction** (`C-068`)

`R6`'s degeneracy is **not bad luck in layer choice.** It *descends* from the cell-B ceiling. The
inherited framing had §69.2 treating *"all six folds picked L=6"* as a coincidence worth
explaining, and §69.3 treating the §13 ceiling as a separate design error. Both are individually
defensible; together they miss that **one property of cell B produces all three.**

### Why this matters for THIS phase, and it is not retrospective

**It explains `R-113`'s healthy selection.** `PR-048` selects on **cell C**, where
`target_surface != target_semantic` in 5,568/5,568 rows — a population where the probe *cannot*
read lexical identity. So the surface does not saturate, `select()` finds a genuine maximum, and
the result was **layer 9, `n_tied = 1/36`, `inert = False`** rather than layer 6 with 36/36 tied.

That was recorded in `R-110` as *"the first non-degenerate layer selection in this project's
recorded history"*, and I treated it as a welcome property. **It is not luck — it is a
consequence of moving the selection population off the saturating cell**, and it now has a
mechanism rather than an observation.

### The operational consequence, which is the peer's actual point

**The fix for §13 and the fix for the inert selection are the same fix**: read the concept signal
at a position that is *not* the concept word. A non-saturating selection population also stops
forcing the grid minimum, which stops landing on the degenerate layer. **One change repairs the
instrument in three places.**

This is now a **binding constraint on `PR-056` (PHASE 8)**: the corrected knockout must not select
on a saturating population *and* must read strictly above the band floor. Those had been treated
as two independent requirements; they are one requirement with two symptoms, and satisfying only
the second would leave the first free to re-create it.

**Credit where due:** the synthesis is the peer's, produced after it had stood down and while
declining to edit anything itself. The verification above is mine, from my own bank, and it
agrees.

## 2026-09-07 · R-114 · the exploratory pair, and **PR-052's premise fails on the rows it is computed over**

`scripts/dcs_ts_exploratory.py`, `reports/DCS_TS_EXPLORATORY.md`. Distinct `--out` per
preregistration (`C-093`), and the writer refuses to overwrite a file holding a different
`prereg_id`. The EXPLORATORY label is **enforced rather than asserted**: the analyzer reads the
`EXPLORATORY` family out of the frozen `multiplicity` block and **refuses to run on any
preregistration that does not place its own id there**, so it cannot be pointed at `PR-048` or
`PR-053` to manufacture a number, and `assert_no_verdict()` refuses to leave confirmatory language
in an artifact.

| | estimate | 95 % t | bootstrap | floor | margin |
|---|---|---|---|---|---|
| **PR-049** knife-vs-gun, unstratified | **0.9446** | [0.9267, 0.9624] | [0.9283, 0.9609] | **0.7065** (re-derived, replicates to 4 dp) | +0.2381 |
| **PR-052** arm-balanced surface cells | **0.9294** | [0.9058, 0.9530] | [0.9073, 0.9519] | **0.5573**, not the frozen 0.5054 | +0.3721 |

Both 23/23 domains; both p-values **at their floors** and reported as such. 17/17 and 19/20 checks,
11/11 and 12/12 mutations RED.

### C-108 · the one failed check is the finding: PR-052's premise does not hold on TEST

`SURFACE-FLOOR-VERIFIED` **FAILS**. Inside the arm-balanced cells the surface classifier reaches
**0.5573, CI [0.5135, 0.6003] — the CI EXCLUDES 0.5** on the test rows. It covers chance on
validation (0.5199, [0.4773, 0.5623]), which is where `Z1` measured it.

So `PR-052` asserts surface information is *verifiably absent* inside the cells, and on the rows
the estimate is actually computed over it is **reduced, not absent** — 0.7065 → 0.5573. That is
the **second** of my preregistrations to rest on a premise that fails when checked (`C-100` was
the first, and it was the same kind of error: asserting a property of a construction instead of
measuring it). Per `PR-052`'s own rule — *"the floor is the measured surface accuracy in the SAME
cells, verified per run"* — the operative bar is **0.5573**, and the margin is +0.3721 rather
than the +0.4240 the frozen number would have implied.

### C-109 · I mislabelled where the 0.5054 floor was measured

`PR-052` **and this log** say the 0.5054 surface floor was measured on *"all 23 **test**
domains"*. **`Z1` never read a test label.** It was **validation** —
`reports/DCS_TS_PR050_PR051_BLOCKERS.md` says so explicitly, and the agent that wrote it scoped
itself to train+validation on instruction. I introduced the error when recording `R-106`/`PR-052`
and it propagated into a frozen config. Corrected here; the frozen files are not edited.

Also carried forward: `PR-049`'s config still shows the superseded 0.963/0.900 power. `C-101`'s
corrected 0.905/0.793 **travels beside it in the artifact** rather than replacing it in the frozen
file.

### C-110 · the occurrence-bug class is EIGHT instances, not seven

I briefed the claim-table agent with "seven". The log's own numbering reaches **"the EIGHTH
instance"** at `C-090`, and counting them out gives `C-075`, `C-076`, `C-079`, `C-080`, `C-087`,
`C-090`, plus `C-095` (the mutation harness that carried no mutation for the gates it certified)
and `R-108` (the same matcher causing a hard extraction refusal). The table names each instance
rather than quoting a bare total, which is the right fix — a count is exactly the kind of thing
that drifts.

## 2026-09-07 · PR-056 and PR-057 · PHASE 8 and PHASE 9 preregistered before anything runs

`configs/dcs_ts_pr056_phase8.json` (corrected attention knockout) and
`configs/dcs_ts_pr057_phase9.json` (**the causal concept-axis intervention — CLAIM C**).

Both verify under the loader: *clean, status FROZEN, 17 hashes pinned and verified, all 12
mandate-§21 fields present*, with every bank/pool/split hash **copied verbatim from `PR-048`** —
no hash invented — and 6/6 mutations producing a refusal on each.

**Both refuse `--for-extraction` right now**, by design: PR-056 gives 6 refusals and PR-057 gives
9, covering every blocking checklist item plus `analyzer_exists: false`. **Nothing can be submitted
until the analyzers exist and the blockers close.** All `blocking`/`done` fields are real booleans,
per `C-086`.

`PR-057` carries the clause that matters: if the probe score moves but the model's interpretation
does not, the finding is **"decodable but not causally used under this intervention"** — which
mandate §32 calls a valuable result — and **never** "the representation is meaningless". It also
records its dependence on the PHASE 7 readout (job 865335) for an outcome variable, without which
the phase would repeat `R-097` exactly: a mediation question with no `y` measured where `x` lives.

## 2026-09-07 · mandate §34 deliverables 12–15 complete

`reports/DCS_TS_CLAIM_TABLE.md` — 20 rows in the mandated columns
`CLAIM | EVIDENCE | N_DOMAINS | TEST POPULATION | CAVEAT | STATUS`, statuses drawn only from the
log's own vocabulary: **7 CONFIRMED, 5 VOID, 4 CANNOT ANSWER, 4 UNTESTED, 2 UNSUPPORTED,
1 NARROWED.** CLAIM A **as worded** is NARROWED; its narrowed form A′ is CONFIRMED; the
codeword-is-special form A″ is **UNSUPPORTED**. CLAIM B is UNSUPPORTED, with a discrimination-only
B′ CONFIRMED carrying the bimodal-null caveat. CLAIM C UNTESTED. CLAIM D UNTESTED, and the
*inherited* whole-query knockout VOID. CLAIM E CANNOT ANSWER. **Installation is listed as an
assumption, not a result** — job 865335 is still in flight.

Plus **18 speakable sentences** with every qualification inline, and a must-not-say list that
reproduces mandate §33 verbatim and then adds **~30** sentences this phase newly made unsayable —
grouped by cause: localisation, separability, p-values at their floors, the 1.8-point margin,
causality and installation, register, the banks and the 113-vs-116 population, and presenting
`R-111`/`R-112`/`R-113` as converging confirmations when one narrows another and one is a negative.

Notably it **bans the mandate's own phrase** *"decodable but not causally used"* for present use —
no intervention exists to license it. That is the right call: §32 offers it as the honest wording
*for a causal result*, and using it now would imply an experiment that has not run.

`reports/DCS_TS_SLACK_DRAFT_MATAN_MAHMOOD_20260907.md` — the collaborator update, ~570 words of
prose, checked against the must-not-say lists (spot-checked here: **0** banned phrases, DRAFT
marker present three times). It answers each of Matan's §3 asks in a line, including the unwelcome
one, and carries the single concrete ask: fund the register-matched regeneration.

**DRAFT ONLY. Nothing was sent — no Slack, no email, no calendar** — and the file says so in its
header and its last line.

---

# 2026-09-07 · R-115 · **ONLY BOMB INSTALLS.** The §15 table materially qualifies R-113.

`scripts/dcs_ts_prompt_validation.py`, `reports/DCS_TS_PROMPT_VALIDATION.md`. 18/18 refusals
reachable; a bare invocation **refuses** rather than defaulting. 21,696 rows, 113 domains, on the
**4 of 6** banks complete at run time (`basket_knife`, `basket_gun` missing; **nothing imputed for
them**, and that is stated rather than smoothed over).

## The finding

Domain-mean `concept_binary_prob ≥ 0.5`, primary channel, cell C, dose 4:

| concept | domains installing | median prob | median `semantic_logodds` | **on R-113's 23 TEST domains** |
|---|---|---|---|---|
| **bomb** | **70 / 113** | 0.576 | **+0.99** | **12 / 23** |
| **knife** | **3 / 113** | 0.140 | **−4.89** | **2 / 23** |
| **gun** | **1 / 113** | 0.030 | **−6.96** | **0 / 23** |

All three show Δ(C−A) > 0 at the permutation floor — **direction yes, level no.** The
demonstrations move the readout in the right direction for every concept; only for **bomb** do they
move it past the point where the model actually reports the concept.

## What this does to `R-113`

`R-113` reported a **three-way** probe at 0.9399, and it separated three classes **two of which do
not install**. So the probe is not distinguishing *which concept was installed* — for knife and gun
there is, by this measurement, **no installed concept to distinguish**. It is distinguishing
**which demonstration set is present**.

That is not a retraction of the number; the number is what it is, and the population and split were
honest. It is a **substantial narrowing of what the number means**, and it converges with `R-112`
from a completely different direction: `R-112` said the signal is not localised at the codeword,
and `R-115` says for two of three arms there is no bound concept for it to be localised *to*.
**Two independent instruments, the same conclusion — the probe reads the prompt.**

`CLAIM A` was already narrowed to a statement about the prompt. It must now also carry: **the
three-way framing overstates what was manipulated.** A bomb-vs-knife contrast is, on this evidence,
a contrast between *an installed concept* and *a demonstration set that failed to install one*.

## The other four findings

**`option_mass`: the channel IS engaged, and the CANNOT-ANSWER trigger does NOT fire.** Median
**0.1137** against the 0.05 gate, p10 0.0221, 95.4 % of rows ≥ 1 % — three to four orders of
magnitude above the ~1e-5 the preregistration feared. No fallback to the display channel is
licensed. ⚠ Qualified honestly: at **dose 0** the median is **0.0372, below the gate**, and 0.11 is
a *minority* of the mass — roughly 89 % of the time the argmax is a third word entirely.

**The codeword matters as much as the concept.** `button_bomb` installs in **92/113** domains;
`basket_bomb` in **46/113** — same concept, same demonstrations, **half the installation**. The
lexical item is not incidental to whether the mapping takes.

**The display channel names the answer in its own question.** *"…does the word button refer to a
button or to a bomb?"* — the concept word appears in `full_prompt` in **100 %** of forced-choice
rows and **0 %** of primary-channel rows. Its more flattering installation numbers (knife 92/113)
are **partly a measurement of the prompt**, which is exactly why `PR-048` made it the display
channel and not the mechanistic one.

**The dose-0 null is clean:** cell A ≡ cell C domain-means to 1e-9 in **113/113** domains, all
concepts, both channels — confirming `C-081` at the level of measured readouts rather than only at
the level of prompt bytes.

## C-111 · a preregistration I referenced and never wrote

The installation cut of 0.5 is **not preregistered**. There is **no `configs/dcs_ts_pr054*.json`
on disk** — I cited `PR-054` in the readout driver's own docstring and never created the file. The
script refuses to apply any cut unless it is passed **and** explicitly acknowledged, and stamps
`installation_rule_source = unregistered_cli` into every row. A sweep from 0.10 to 0.90 shows the
bomb ≫ {knife, gun} ordering holds **at every cut**, so the conclusion does not depend on the
threshold — but the gap is real and it is mine. **PHASE 9 must close it before extraction.**

Nothing was filtered: full distributions are reported and installation is a **stratification
variable**, per mandate §15.

## 2026-09-07 · B-021 · the PHASE 9 analyzer is built, and it found five blockers **in my own design**

`scripts/dcs_ts_pr057_causal.py`, `reports/DCS_TS_PR057_DESIGN.md`. **`--self-test` 46 checks,
0 failed; `--mutate` 21/21 RED; `--plan` enumerates 54 arms** (24 live, 30 control), 230 rows/arm
on TEST, with per-arm launch commands. Default invocation **refuses** (no arm has run);
`--for-extraction` refuses on 8 blocking items. Config and mandate §10 were checked against each
other and **agree on every clause**, so nothing was chosen between them.

The self-test includes the things that actually matter here: a deliberately **disabled hook**
reproduces its input exactly, passes as a bridge, and is **REFUSED when presented as live**; a dead
hook, a zero-norm direction and a zero-magnitude edit are each caught; the `C-068`
read-at-the-edit-layer case is caught; domain-level permutation recovers a planted shift and
centres at 0; and dropping any one of the four success conditions yields 3/4 with `success=False`.
The literal negative wording is asserted as a string so it cannot drift.

**Five blocking findings, all in work I specified:**

**Q9 — the preregistered O2 is NOT COMPUTABLE.** `score_behavior` asserts one concept/codeword pair
per bank and builds its answer set from `rows[0]`, so **there is no `logP(knife)` on a bomb bank**.
`PR-057`'s O2 — source-vs-target concept log-odds, which is how success condition 2 was to be
measured — **cannot be formed at all** on this data layout. The analyzer returns
`computable=False`, reports the companion `semantic_logodds` explicitly labelled as unable to
satisfy condition 2, and **refuses to emit a verdict**. I preregistered an outcome the pipeline
cannot produce; better found now than after a GPU run.

**Q13 — the controls would have been norm-matched to the WRONG direction.**
`make_intervention`'s `random` and `orthogonal` controls derive from `payload["d_surface"]`.
Unless the `PR-053` payload aliases that to `v_bomb_specific`, **C1 and C4 are matched to a
different base direction while looking correct in every log.** That is precisely the silent-failure
shape this phase has found eight times, and it would have produced a clean-looking control that
controlled for nothing.

**Q12 — an S1 arm launched today would silently be an all-position edit.** `make_intervention` only
ever builds `AllPositionProjectOut`; `score_behavior` also lacks the cross-prompt donor, a
`component_replace` mode and a disable-hooks flag. The single-site scope of §10.4 does not exist
yet.

**Q10** — `PR-048` persists `SELECTION_TRACE` and accuracies but **not the fitted coefficients**,
so O1 has no frozen probe artifact. **Q11** — `extract_boombness.py` has no `--intervene`, so O1
must be captured inside the intervention run.

**Cost when unblocked:** 12,420 rows, ~1.5–2 GPU-hours, `--time=06:00:00`, derived from a measured
2.42 rows/s — with the exact `sbatch` line, `BOOMB_EXPECT` and `BOOMB_REQUIRE_ARGS=1` set, and a
shared-FS argsfile.

**CLAIM C remains UNTESTED, and is now blocked on five concrete, named things rather than on
"we didn't get to it".** That is a better place to be, and the honest read is that `PR-057` was
preregistered against a pipeline that cannot yet execute it.

## 2026-09-07 · PR-054 · closing `C-111` **without pretending to preregister a threshold I had already seen**

`configs/dcs_ts_pr054.json`, FROZEN, loads clean.

`C-111` was that I cited `PR-054` in the readout driver's docstring and never wrote it, so `R-115`'s
0.5 installation cut ran under no preregistration. The obvious repair — write the file now and name
0.5 — **would have been worse than leaving the gap open.** I have already seen the installation
numbers on four of six banks. Preregistering a threshold after seeing the data it will be applied
to is not a preregistration, and calling it one would launder a post-hoc choice into a frozen file.

**So the threshold is removed rather than defended.** The primary reporting mode is **the full
sweep, 0.10 → 0.90 in steps of 0.05**, per concept, per codeword, per split. `R-115` already
measured that the bomb ≫ {knife, gun} ordering holds **at every cut in that range** — so no
threshold is load-bearing for any conclusion drawn, which means there is no reason to pick one, and
picking one would import a degree of freedom the analysis does not need. **0.5 survives only as a
labelled reference point for prose**, and every use of it must carry the words *"chosen after
seeing four of six banks"*.

Two further things the file fixes:

**The measure is a within-prompt contrast, C minus A**, against the byte-identical baseline — so
its nuisance floor is **0.0 by construction**, exactly as in `PR-051`, and surface confounds
common to both cells difference out. Installation is never an absolute level against an arbitrary
bar.

**The §15 prohibition is written in as absolute.** Installation is a **stratification variable**;
it is **never** a post-hoc exclusion, in this phase or a later one. No domain may be dropped for
failing to install. *If a result holds only on installing domains, that is a finding to state, not
a population to quietly adopt.* The analyzer enforces it by reporting full distributions and
refusing to emit a filtered population.

The file says of itself, in its own `artifacts` block, that it was written **after** the readout ran
and after partial results were seen, that it specifies **reporting** rather than a hypothesis test,
and that it is labelled so throughout precisely so it cannot be mistaken for the latter.

**Two blocking items remain on it:** rerun the table on all **six** banks (`R-115` used four), and
report the sweep rather than a single cut.

## 2026-09-07 · C-112 · **R-115 compromises PHASE 9's upper-bound patch, and that has to be faced before spending GPU**

Mandate §10.1 specifies the upper-bound test as: patch the **C_knife** representation into a
**C_bomb** target and ask whether the semantic interpretation shifts **bomb → knife**.

**`R-115` makes that arm largely uninterpretable.** Knife installs in **3 of 113** domains
(median `semantic_logodds` **−4.89**); gun in **1 of 113** (−6.96); on the 23 test domains,
**2/23 and 0/23**. So the donor representation is not "a prompt where knife is installed" — it is,
for ~97 % of domains, **a prompt where a knife demonstration set failed to install anything**.

Patching that in and observing no shift toward knife would be **exactly what you would expect
whether or not the concept axis is causally used.** The arm cannot distinguish its own hypotheses.
Running it as specified would produce a null that reads as evidence and is not.

**Consequence, decided now rather than after the run:**

- **§10.1 (patch) is DEMOTED to exploratory**, and its null is **CANNOT ANSWER by construction**
  on this corpus — for the same structural reason `C-074` was: the manipulation the arm depends on
  is absent. It may still be run for the ~3 domains where knife does install, reported as an
  n=3 observation and nothing more.
- **§10.2 (surgical subspace intervention) becomes the primary causal test**, and it is
  **unaffected** by `R-115`. Projecting `v_bomb_specific` out of a **bomb** prompt — where the
  concept demonstrably *does* install in 70/113 domains — and asking whether the bomb readout falls
  is a well-posed question that needs no donor and no second installed concept. The four-part
  success rule of §10.5 applies to it unchanged.

**This is the second time `R-115` has changed the meaning of a design rather than a number**, and
both times in the same direction: the three-way framing assumed three installed concepts, and there
is one. `R-113`'s interpretation narrowed; `PHASE 9`'s primary arm moves from the patch to the
projection.

Worth stating plainly: had the readout run *before* the probe — the ordering the mandate's own
PHASE list implies, with PHASE 7 ahead of the analysis phases — this would have been known before
`PR-048` was designed as a three-way contrast at all. **The phase ran its confirmatory analysis
before its validation instrument**, and the cost is that two designs had to be reinterpreted after
the fact rather than built correctly the first time.

---

# 2026-09-07 · R-116 · the §15 table on **all six banks** — supersedes `R-115`, and knife is **zero**

Job 865335 `COMPLETED 0:0` in 3:40:27, 6/6 banks. Table rerun on the full population: **32,544
rows, 113 domains**, coverage `6/6 COMPLETE`. The only failures are 16 per *basket* bank, all
`school_campus`, all the `C-075` `basketball` case — an excluded domain, so accepted; the analyzer
would have refused a short domain that was not an exclusion.

## Installation, primary (concept-free) channel — `semantic_one_word`, cell C, dose 4

| concept | median `concept_binary_prob` | median `semantic_logodds` | domains installing (113) | **on the 23 TEST domains** |
|---|---|---|---|---|
| **bomb** | **0.7284** | **+0.99** | **0.619** | **0.522** |
| **knife** | 0.0011 | **−6.83** | **0.000** | **0.000** |
| **gun** | 0.0006 | −7.38 | 0.009 | **0.000** |

**On six banks, knife installs in ZERO of 113 domains.** `R-115` reported 3/113 from four banks;
the full population removes even those. **`R-115` is superseded — the finding is stronger, not
weaker.**

The nulls are exact: at **dose 0**, bomb's `concept_binary_prob` is **0.0000** with log-odds
**−14.52**; in **cell A** at dose 4 it is **0.0000**, −12.56. The instrument reads nothing where
there is nothing to read.

## The result that most deserves to be shown to Matan

**The same rows, scored through the two channels:**

| concept | primary (concept-free) — domains installing | **display (forced choice)** — domains installing |
|---|---|---|
| bomb | 0.619 | 0.991 |
| **knife** | **0.000** | **0.628** |
| gun | 0.009 | 0.088 |

**The display channel says knife installs in 63 % of domains. The concept-free channel says zero.**
The entire difference is that forced choice **names the answer in its own question** — *"does the
word button refer to a button or to a knife?"* — and the concept word appears in `full_prompt` on
**100 %** of forced-choice rows against **0 %** of primary-channel rows.

Had the display channel been primary, this phase would have reported that all three concepts
install and that the three-way probe measures concept identity. **The `PR-048` decision to make the
concept-free channel primary — recorded before any of this was visible, with the known risk that
its absolute option mass might be too small to use — is what stopped that.**

## The decoded answers, which need no statistics

Top answers, primary channel, cell C, dose 4:

- **bomb** → **` Bomb` 779**, ` Alarm` 119, ` Basket` 97, ` Gren` 91, ` Explos` 80
- **knife** → ` Container` 348, ` Basket` 324, ` Button` 208, ` Fast` 190 — **never ` Knife`**
- **gun** → ` Basket` 295, ` Button` 247, ` A` 118, ` Container` 117 — **never ` Gun`**
- cell A, all three → ` Basket` 295, ` Button` 140, ` A` 126 … (identical, as the byte-identical baseline requires)

Asked *"what does the word button actually refer to?"*, the model answers **"Bomb"** when bomb was
demonstrated, and answers **with the codeword itself** when knife or gun was. That is Matan's own
question (§3.7), answered directly and without a statistic.

⚠ And on the display channel, ` Knife` is chosen **502 times in cell A** — the *benign baseline*,
where no knife demonstration exists at all. The option being named is doing the work.

## Option mass — the channel is engaged

Primary cell median **0.1138** against the 0.05 gate; 95.5 % of rows carry ≥1 % of the next-token
mass; p10 = 0.0227. **Three to four orders of magnitude above the ~1e-5 the phase recorded as its
worry before running, so the preregistered CANNOT-ANSWER trigger does NOT fire.** Per concept:
bomb 0.1591, knife 0.1156, gun 0.0934. ⚠ Still a *minority* of the mass — most of the time the
preferred answer is a third word, and dose-0 rows sit at 0.0328, **below** the gate.

## Threshold independence, and the codeword

The sweep `PR-054` made primary: at a cut of **0.10** the counts are 109 / 17 / 49; at **0.90**
they are 4 / 0 / 0. **The bomb ≫ {knife, gun} ordering holds across the whole range**, so no
conclusion here rests on the 0.5 reference point. `PR-054`'s **I-A and I-B are closed.**

**The codeword remains as consequential as the concept**, now on six banks: `button_bomb` installs
in **92/113** domains, `basket_bomb` in **46/113** — same concept, same demonstrations, **exactly
half**.

## 2026-09-07 · the §34 deliverables updated for `R-116`

Both were written while installation was still an assumption. Revised in place:

**The installation row moves from `UNTESTED` to `UNSUPPORTED` as worded** — for knife and gun;
bomb installs. It now carries the six-bank numbers per concept and **explicitly never pooled**,
plus the Δ(C−A) > 0 *"direction yes, level no"* line and the exact nulls.

**CLAIM A is now marked narrowed TWICE, by two independent instruments** — `R-112` (not localised
at the codeword) and `R-116` (for knife and gun there is no installed concept for it to be bound
to). `CLAIM A′` keeps 0.9399 and its status: **the number stands, its object changes.**

**Three rows added**: the two-channel comparison, the decoded answers (§3.7), and the codeword
effect. **`CLAIM C` stays `UNTESTED`** — no intervention has run — with `C-112` recorded against it.

**Nine new must-not-say bans**, the important ones being: *"the demonstrations install the
concept"* (now measured false for two of three), pooling 0.619/0.000/0.009 into a
*"partial/weak installation"* gradient, quoting the display channel's flattering knife 0.628 as an
installation number, *"the three-way probe measures concept identity"*, presenting 0.5 as
preregistered, and treating §10.1's patch as the causal test.

Three tempting framings were **deliberately kept out of the draft and written into the ban list
instead** rather than softened into it. Compliance re-checked here: the draft's single hit on my
banned-phrase grep is the sentence *"a null there would look identical whether or not the axis is
causally used"* — which is the **explanation of why the patch arm is uninterpretable**, not a claim
of causal use. Legitimate. DRAFT markers intact; **nothing sent**.

⚠ One deviation from my own instruction, recorded rather than hidden: I asked for the draft to stay
near its existing length and it grew from ~830 to ~1,190 words. The added material is the
installation result, the channel comparison and the decoded answers — all of which earn their
space — and weaker content was cut to partly offset it. But it is now a long message rather than a
short one, and that was my constraint to hold.

---

## DCS-R-117 — PHASE 9 checklist Q0 is CLEARED, and the 16 rows that were not missing
*2026-09-07*

All six `ts116m` banks have now landed the PHASE 7 readout (3/6 when `DCS_TS_PR057_DESIGN.md` was
written). `option_mass_gate = PASS` and `reportable = true` on **6/6**, with `semantic_one_word`
median true mass 0.059-0.086. The preregistered branch "a disengaged primary channel is a CANNOT
ANSWER, not a licence to fall back on the display channel" is therefore **not** taken.

The row counts disagreed: button banks 5568, basket banks 5552. The prompt banks are identical in
size (22272) and carry the same 116 domains with an empty symmetric difference, so the 16-row gap
arose **during scoring**. Chased rather than tolerated, per the standing rule that two disagreeing
counts get checked at corpus, instrument and population before either is believed.

It resolves **entirely** to the single domain `school_campus` (button 48, basket 32) -- one of the
three whole-population exclusions, so it cannot reach any result. Restricted to the 113 analysed
domains all six banks are exactly balanced: **5424 rows each**, identical
(cell x query_kind x n_examples) profile, {0: 226, 4: 1130} per cell per channel.

This was worth the time precisely because the same 16 rows landing inside an analysed domain would
have been a defect, and the two cases are indistinguishable without looking.

Population arithmetic cross-checks independently: cell C / `semantic_one_word` / `n_examples=4` =
1130 rows per bank over 113 domains = 10 rows per domain; TEST is 23 domains, giving **230 rows per
arm**, which is the number `DCS_TS_PR057_DESIGN.md` section 2 states from the other direction.

Q0 signs off instrument liveness and population balance and **nothing else**. It is not evidence
against R-116's installation asymmetry (bomb 0.619, gun 0.009, knife 0.000) and must not be quoted
as though it were. Written up in `reports/DCS_TS_PHASE9_Q0_SIGNOFF.md`.

## DCS-R-118 — PHASE 9 checklist Q2 is CLOSED: the direction exists and reproduces R-111
*2026-09-07*

`v_bomb_specific` now exists on disk in the format the CONSUMER reads, which is the only format
that matters. `outputs/dcs_ts/directions_pr053/directions_fit_dev.pt`, written by
`scripts/dcs_ts_export_directions.py`, which **imports** its estimator from
`scripts/dcs_ts_pr053_diffmeans.py` rather than reimplementing it.

The format was derived from `score_behavior.py:2081-2085` -- which joins `--fit-dir` with the
literal filename `directions_fit_dev.pt` and indexes
`payload[<name>][<int layer>] -> Tensor[H]`, with `payload["gap"]` for `add` dosing and
`payload["cell_means"]` for realised dose -- not guessed from the writer. Vectors are stored UNIT
with the raw diff-of-means norm in `gap`, because this call site doses `add` in GAP UNITS and the
config records that getting this wrong was already missed once at this exact second call site.

**TRAIN only, asserted as equality not disjointness.** The fit set must EQUAL the frozen manifest's
67 train domains; a population that grew *or shrank* refuses. Disjointness from validation and test
is checked separately.

**It reproduces the published result**: reloaded from disk and re-scored on the 23 untouched TEST
domains, band-mean AUROC **0.976401** vs R-111's published 0.9764, CI [0.962219, 0.990583] vs
[0.9622, 0.9906], sd 0.034703 vs 0.0347, 23/23 domains above chance, per-layer profile identical at
all nine layers. 25/25 checks GREEN, **20/20 mutations RED** (including TRAIN+TEST leakage,
fit-on-validation, TRAIN-1 domain, the residual axis swapped for the raw axis, a 1e-4 perturbation,
and a one-layer rotation catching an off-by-one convention error).

**The R-116 caveat travels with the file.** `v_knife` and `v_gun` are differences over demonstration
sets that install nothing, so the two subtracted terms are not "the knife and gun concepts" -- they
are the common mode of non-installing harm demonstrations. The subtraction is doing real work
(`cos(v_bomb_specific, v_remap)` is only 0.22-0.44 across the band, so this is not a rescaled
`v_bomb`) and it discriminates at 0.976. What it does **not** license is reading a projection-out
result as being about concept identity alone. Recorded as `meta.interpretation_warning` inside the
payload so it cannot be separated from the artifact.

Definition unchanged: exported exactly as PR-053 froze it. The issue is flagged, not fixed.

## DCS-C-113 — the FROZEN phase-9 config names a directions path that can never load
*2026-09-07* -- defect, recorded, config NOT edited

`configs/dcs_ts_pr057_phase9.json` `directions.artifact.path` reads
`outputs/dcs_ts_pr053_diffmeans/<run>/directions.pt`. That path cannot ever load: the consumer
(`score_behavior.py`) does not accept a file path at all -- it takes a DIRECTORY via `--fit-dir`
and joins the fixed filename `directions_fit_dev.pt` itself. The loader, not the preregistration,
fixes the filename.

**Impact is documentation-only, and this was checked rather than assumed.** The config deliberately
writes NO `*_sha16` for this artifact -- its own `pin_rule` explains that a null hash would
correctly make the preregistration unloadable and an invented one would be worse -- and the path is
not under `population.banks` or `population.pools`, which are the only places
`dcs_ts_prereg.validate()` checks paths on disk. So the loader does not refuse, and PHASE 9 is not
blocked by it.

The config is FROZEN and was **not** edited. The binding requirement Q2 actually imposes is
unaffected and is met: the analyzer recomputes the direction file's sha256 at load and writes it
into every run artifact, so the direction actually used stays recoverable from the output even
though it could not be pinned in advance.

The correct `--fit-dir` argument for every PHASE 9 job is therefore
**`--fit-dir outputs/dcs_ts/directions_pr053`**, not the path the config prints.

---

## DCS-C-114 — the claim table cites a report that does not contain its numbers
*2026-09-07* — provenance defect, found by a universal-quantifier sweep, fix in flight

`reports/DCS_TS_CLAIM_TABLE.md` and this log both cite
`reports/DCS_TS_PROMPT_VALIDATION.md` as the source for **R-116**: six banks, 32,544 rows, and the
headline that **knife installs in 0 of 113 domains, superseding R-115's 3/113 from four banks**.

The file on disk is the **superseded four-bank table**. Its own line 26 reads *"Job 865335 was
still running when this table was built. Four of six banks are analysed; two are ..."* and line 50
reads *"21,696 rows, 113 domains x 4 banks"*. Its primary-channel table gives knife **3/113**
(train 1/67, val 0/23, test 2/23) with max 0.695.

So a reader who follows the citation finds **3/113 where the claim says 0.000**. The claim is
believed correct and the cited artifact is stale — which is the more dangerous direction of this
failure, because every number in the claim table is defensible and the audit trail still fails.

**How it was found, and a near-miss worth recording.** A universal-quantifier sweep over my own new
text (grep for every/all/none/never and ask only "does this name its population?") led to checking
the exclusion constants, which led to reading the source report. Reading only that report, I
concluded the opposite: that "knife 0.000" was **false**, that the true figure was 3/113, and that
I had been propagating an error into commit messages and the collaborator draft. The reasoning was
concrete — knife's max of 0.695 exceeds the 0.5 cut, which *proves* at least one domain installs —
and it was wrong, because it was reasoning about the wrong population. This log's own R-116 entry
records the supersession explicitly. **Two artifacts disagreed and I nearly "corrected" the right
one to match the stale one.** The rule that saved it is the standing one: when two counts disagree,
check corpus, then instrument, then population, before believing either.

The mechanism of the supersession is counterintuitive enough to need verifying rather than
believing — adding banks should not *reduce* an installation count. The hypothesis under test is
that the statistic is a domain-mean pooled across each concept's TWO banks, so the three domains
that passed on `button_knife` alone fall under 0.5 once `basket_knife` is averaged in. That is
being confirmed or refuted against the actual per-bank numbers, not assumed.

**Fix:** regenerate the report on all six complete banks (all six now carry `DONE.json` with status
ok and `option_mass_gate` PASS — verified under R-117), require it to state its own bank and row
counts in its header so this cannot recur silently, and re-verify every number the claim table
asserts against it. Instruction given: **if any number disagrees, stop and report it — do not adjust
anything to make them agree.**

## DCS-A-046 — the remaining phases, and the two that are DECISIONS rather than states
*2026-09-07*

Written up in `reports/DCS_TS_REMAINING_PHASES_GATING.md`. Of the mandate's fourteen phases, 1-7
are complete, 9 is in flight with 7 of 12 blockers closed, and:

**PHASE 8 is DEFERRED, not skipped.** Its analyzer does not exist and its FROZEN config returns 6
refusals under `--for-extraction`, so it cannot run today regardless of scheduling. PHASE 9's
item **Q8** asks only that PHASE 8 be "completed or explicitly deferred so the two GPU phases do not
compete for fair-share" — this is that deferral, for the reason Q8 names. **Q8 satisfied.**
`A-045`'s constraint carries forward: read strictly above the band floor AND do not select on a
saturating population, which are ONE requirement.

**PHASE 12 is GATED OFF by its own written precondition.** The mandate does not list it
unconditionally: *"PHASE 12 — **Only if representation story is solid:** row-randomized behavioural
controls; mapping_use; ASR."* The representation story is not solid, and this phase's own results
are what established that: `R-112` narrows CLAIM A from the codeword to the prompt (control 0.9261
vs codeword 0.9446, **both** p-values failing preregistered Holm); `R-116` shows two of three arms
never install; CLAIM B is UNSUPPORTED after `R-111`'s question D failed. A precondition written into
the mandate is not a hurdle to be argued past. It reopens only on a PHASE 9 positive, and even then
the installation asymmetry must be handled first, because an ASR number computed over arms that
never installed their concept is uninterpretable in exactly the way section 33 bans.

PHASES 10 and 11 are runnable but unstarted (zero prior mentions in this log); PHASE 11 reuses the
four existing k-ladder scripts rather than starting from nothing, with the *concept-free* readout
as the new part — which is precisely what `R-116` showed matters, the display channel taking knife
from 0.000 to 0.628 purely by naming "knife" in its own question. PHASE 13 is blocked on PHASE 9 by
construction. PHASE 14 runs continuously; its **literature update is outstanding** and is named here
so it is not quietly dropped.

## DCS-C-115 — a background waiter I wrote committed 7 files under a 3-file message
*2026-09-07* — process defect, mine, no foreign work taken

Commit `30c3128b` is titled *"DCS: fold R-116 into the section-34 deliverables"* and contains
**seven** files, including `DCS_TS_PHASE9_BLOCKERS_CLEARED.md`, `DCS_TS_PHASE9_Q0_SIGNOFF.md` and
`dcs_ts_export_directions.py`, none of which that message describes.

Cause: a background waiter **I wrote in an earlier turn** — a loop that waits for git to be free and
then commits — used `git commit -q -m "..."` with **no `--` pathspec**. The standing rule in this
tree is that only `git commit -- <paths>` is safe, and I applied it to my foreground commands while
leaving it out of the one that ran unattended. Everything swept was my own, so no other writer's
work was taken; the message misdescribes the commit permanently.

Second-order effect: that waiter starved for ~40 minutes because its "is git busy" guard matched my
own foreground `git status`/`git add` calls, then fired at the worst possible moment — concurrently
with my second commit, which died on `cannot lock ref 'HEAD': is at 30c3128b but expected
2a478209`, rc=128. **Git refused rather than clobbering, which is the correct outcome**, and the
three code files simply stayed uncommitted until this entry's commit.

Rule updated: the path-limit applies to commands written for **later, unattended** execution, not
only to the ones typed now — and never leave such a waiter queued while continuing to use git.

---

## DCS-R-119 — C-114 fixed: the six-bank table regenerated, every asserted number reproduced
*2026-09-07*

`reports/DCS_TS_PROMPT_VALIDATION.md` is now the **six-bank** table: **32,544 rows, 113 domains,
6/6 banks** (was 21,696 / 4 banks). Its header carries a boxed scope block stating bank, row and
domain counts plus the `C-114` history, so a citing reader sees the coverage **before** any number
— which is the specific defect that must not recur silently.

Row arithmetic stated and checked: 6 x 5568 = 33,360 attempted − 48 `basket` failures − 816
exclusion rows = **32,544** = 6 x (113 x 48). Provenance confirmed independently:
`outputs/boombness/logs/boomb_865335.out` names exactly these six run dirs and ends
`all 6 bank(s) completed`.

**Every number the claim table asserts reproduced**, computed twice — once by the script, once by an
independent scratch reimplementation reading only `results.jsonl` and the split manifest: primary
70/113, 0/113, 1/113 (= 0.619 / 0.000 / 0.009); TEST 12/23, 0/23, 0/23; median log-odds +0.9868 /
−6.8300 / −7.3791; display 112 / 71 / 10 of 113; option_mass 0.11376, 95.52% ≥ 1%, dose-0 0.03281;
button_bomb 92 vs basket_bomb 46; the decoded-answer counts; leakage 100% display / 0% primary
across all 32,544 rows. **No disagreement. Nothing was adjusted.**

**The 3 → 0 supersession is CONFIRMED, with the mechanism measured rather than assumed.** The
statistic is a domain mean pooled across each concept's two banks. `basket_knife` installs in
**0/113** on its own (median 0.0086); `button_knife` in 3/113 (median 0.1403). Pooling drags all
three former passers under the cut — `cheese_dairy` 0.6946/0.0185 → **0.3565**, `lab_safety`
0.5810/0.1550 → **0.3680**, `bakery_plant` 0.5062/0.0118 → **0.2590** — and knife's pooled max is
**0.3680**, so the zero is not a near-miss. The control cases behave consistently: bomb pools 92 and
46 into an intermediate 70, and gun's single domain passes in *both* banks so pooling leaves it at
1/113. **`R-115`'s "knife 3/113" was a `button_knife`-only number reported as a knife number** — a
population change, not a re-scoring.

## DCS-C-116 — a transposed triple and an over-broad quantifier in a published deliverable
*2026-09-07* — both corrected in place

The regeneration was told to report anything the new table does **not** support. It found two, both
in `reports/DCS_TS_CLAIM_TABLE.md` row 42, and both are the kinds this project keeps recording.

**(1) A transposition.** The row read *"the ordering holds at every cut (0.10 → 109/17/49 ...)"*
while every other figure in that same row is given **bomb/knife/gun**. Read in the row's own order
that says knife = 17 and gun = 49, which is backwards; the true triple is **109/49/17**. The written
triple is correct only in the **superseded four-bank table's** column order (bomb|gun|knife) — it
was copied across without re-ordering. A stale artifact does not only make citations fail; its
*column order* propagates into text that never mentions it.

**(2) An over-broad universal.** *"The ordering holds at every cut"* is false as written. Only
**bomb ≫ {knife, gun}** holds at every cut. Knife and gun **reverse** across the sweep: knife > gun
at 0.10 and 0.25, gun > knife at 0.50 (1 vs 0), tied at 0 above — because knife's distribution sits
higher in the body (median 0.087 vs 0.032) but has a lower max (0.368 vs 0.717). The only claim that
survives the whole sweep is **"neither knife nor gun installs"**.

This is the universal-quantifier failure exactly: a sentence with *every* in it that does not name
the population it holds over. Corrected in the claim table (with the full sweep now printed and the
correction labelled) and in the collaborator draft, which carried the same over-broad sentence.
**The draft has not been sent; DRAFT markers intact.**

Also recorded, not fixed: no run artifact carries the SLURM job id — `DONE.json`/`config.json` record
only `run_id`, so "job 865335" is verifiable *solely* through `outputs/boombness/logs/boomb_865335.out`.
The citation chain there is the log, not the artifact.

## DCS-A-047 — PHASE 14 literature update, and the ceiling it puts on PHASE 9
*2026-09-07* — `reports/DCS_TS_PHASE14_LITERATURE_UPDATE.md`

The outstanding PHASE 14 component named in `A-046`. Provenance is stated in the file: search results
plus one full-text fetch, one summary from a small model, and **nothing from it used as a
measurement or a threshold**.

Three results bear directly on PHASE 9, and all three had to be recorded **before** the run:

- **`arXiv:2311.17030`** (subspace-patching interpretability illusion) is about exactly the
  intervention H2a performs. A subspace effect can run through **dormant or disconnected** features
  that correlate with the behaviour but sit off the causal path. **A positive H2a would not by
  itself establish causal use.** Our H1-first launch order is precisely the "compare against full
  activation patching" control this literature asks for; what we lack is cross-model replication
  (Llama-only by decision) and any downstream-connectivity test.
- **`arXiv:2605.04061`** reports single-position intervention at **0% task transfer across all 28
  layers of Llama-3.2-3B despite 100% probing accuracy** — same model family, same geometry as our
  **S1**. S1 nulls are the *expected* result, so an S1-only null is **uninformative** and must not be
  reported as evidence of non-use. Our preregistration already declared S1 and S2 as distinct
  hypotheses with that interpretation written in advance.
- **`arXiv:2512.03771`** describes this attack under the name **"Doublespeak"** — the closest
  published neighbour to this project. It reframes our contribution: not that doublespeak exists,
  but the measurement discipline around whether the remapped representation is *used*, plus two
  negatives that literature does not report (`R-112`, `R-116`).

**The convergence with our own adversarial review is the important part.** Measured from our exported
vectors: `cos(v_knife, v_gun) = 0.91–0.95` at every layer — the two subtracted terms are **one
generic demonstration-presence axis measured twice** — and projecting the axis out removes only
**4.7–19.0%** of the cell-mean spread, leaving 78–96% of `v_bomb` intact. So **both outcomes are
bounded**: a positive is unattributable to identity content, and a null sits under a 5–19% dose.

The sharpest point is the reviewer's: `meta.interpretation_warning` guards **only the null**. A
caveat that fires only against the result you did not want is not a caveat. Making it symmetric is a
preregistration-integrity item, and it is open.

---

## DCS-R-120 — Q4b: the PHASE 9 GPU runner exists, and only 26 of 54 arms can be built
*2026-09-07* — `src/boombness/pr057_run_causal.py`, `reports/DCS_TS_PR057_RUNNER.md`

The runner loads the model **once** and loops the manifest; 54 separate `score_behavior`
invocations would spend more wall time loading weights than computing. It **imports** the arm
manifest, hooks, gates and donor contract from `scripts/dcs_ts_pr057_causal.py` and cross-checks
every argv it builds against the analyzer's own `launch_command()`, so the runner and the analyzer
cannot drift into two files that disagree about what an arm is.

Verified, and I re-ran the two harnesses myself rather than accept the report: **`--self-test`
49 checks / 0 failed** (post-rename, bound to the real artifact `sha=0d59b255…`, `fit_domains=67`),
**`--mutate` 26/26 RED**, **`--plan` 54 arms (24 live / 30 control)** reproducing the design doc
exactly. Targeted pytest 113/113; the wider 26-file run did **not** complete (115 passed when
cancelled under three-way node contention) and is stated as such rather than rounded up to "green".

**THE STRUCTURAL FINDING: 26 constructible, 28 not.** Constructible are H2a (4), C1 norm-matched
random (20), C3 raw axis (2). Not constructible: **H1 (16) and C7 (2)** — no `patch` path *and an
empty donor population under R-116*; H2b (4) — no `component_replace`; C2 (2) — no shuffled-label
direction; C4 (2) — `add` is uninstrumented with no single-site form; C5 (2) — `C-119`.

**Why the H1 loss is the one that matters**, and it is a scientific loss rather than a wiring one:
H1's donor is a `C_knife` prompt and knife installs in **0 of 113 domains**, so there is no
knife-installed donor to patch from. `C-112` demoted this arm; the plan shows the demotion is total.
H1 is also *precisely* the control the interpretability-illusion literature asks for (`A-047`,
`arXiv:2311.17030`): comparing a subspace edit against full activation patching at the same site.
With it unavailable, **a positive H2a cannot be validated against its own upper bound.**

Combined with `A-047`'s two measured bounds, PHASE 9 as constructible can return either a **null**
interpretable only with its 4.7–19.0% realised dose attached, or a **positive** attributable neither
to concept identity nor checkable against an upper bound. Written up in
`reports/DCS_TS_PHASE9_CONSTRUCTIBILITY.md` **before** submission, because a scope limit recorded
after a result reads as an excuse.

## DCS-C-117 / C-118 / C-119 — three defects that must close before any GPU time
*2026-09-07* — found by building the arms, which is the only way they surface

- **`C-117` — the liveness producer and consumer do not share a schema. BLOCKING.**
  `pair_common.hook_stats_dict()` writes no `n_cells_edited_expected`, and the analyzer's
  `liveness_gate()` reads a missing count as "the arm declared no destinations" and **VOIDs the
  arm** — so *every* arm would be VOID at analysis time, for a schema reason rather than a
  scientific one. It also writes `resolved_absolute_index` as a **list** and leaves `rel_end`
  **None** on an all-position (S2) edit, while `audit_end_relative()` calls `int()` on both. This
  would have burned the GPU allocation and returned nothing.
- **`C-118` — `--emit-probe` is refused.** `ProbeReadCapture` is a read hook on a layer and
  `score_behavior` exposes no per-row callback; one row produces many forwards, so order-based
  attribution would be exactly the silent misalignment this phase refuses. Independently,
  `outputs/dcs_ts/pr048_result.json` carries **no `FROZEN_PROBE` block** — the analysis has not been
  re-run since Q10 added the export. O1 is therefore not capturable.
- **`C-119` — control C5 certifies nothing at its preregistered α=0.** The bridge is the live arm's
  hook run with its write discarded, and the liveness check refuses a bridge whose inner hook would
  not have edited anything. Refused rather than silently re-dosed to α=1. This is **not cosmetic**:
  the frozen config lists *"the disabled-hook bridge not reproducing baseline"* under `primary.void`,
  so a void condition that cannot be evaluated is a hole in the validity argument.

**Renumbering, recorded not silent.** These arrived from the runner work labelled `C-114`/`C-115`/
`C-116`, IDs already taken the same day by unrelated defects. Renumbered to `C-117`/`C-118`/`C-119`
in the report and in the runner's own `DEFECT_*` constants and self-test labels — code and report
citing different IDs for one defect is the drift this phase punishes. A defect ID is a citation
target, so the collision is named rather than quietly fixed.

## DCS-R-121 — F-1 closed: the direction artifact now verifies its own TRAIN-only property
*2026-09-07*

The adversarial review's F-1 was that TRAIN-only was enforced **only** through `meta.fit_domains`,
a field the producer writes about itself — the project's recorded *"a check that reads the same
broken source"* class. `check_train_only_recomputation()` now re-derives every direction from the
TRAIN rows, rebuilding the TRAIN set from the frozen split manifest and **never** from
`meta.fit_domains`, and separately asserts the metadata matches that manifest set.

Measured residuals: honest fit **7.186e-09** (float32 storage floor), leaked mutant **1.121e-02** —
reproducing inside the harness the leak signature the reviewer had measured externally. Tolerance
1e-6, ~140x above the floor and ~4 orders below the leak, justified from those two numbers rather
than picked.

**Mutations 20/20 → 22/22 RED.** The decisive one: "arrays LEAKED (TRAIN+TEST) while
`meta.fit_domains` still reports the 67 TRAIN domains" turns **exactly one** check red — the new
recomputation row — with every metadata check, the algebra check and `content_sha256` staying
GREEN. That is F-1's prediction confirmed: it would have passed all 26 previous checks. Self-test
16/16 → 21/21; checks 26 → 28, and the count is now **printed by the script** rather than
hand-typed anywhere.

Payload **bit-identical** (`content_sha256 = 8df3fdec…`). The shipped `.pt` was deliberately not
re-exported: that would have changed only `meta.written_utc`, but with it the `payload_sha256`
already published — correct call.

## DCS-A-048 — PHASES 10 and 11 preregistered before anything runs
*2026-09-07* — `configs/dcs_ts_pr058_phase10.json`, `configs/dcs_ts_pr059_phase11.json`

Both verified by me directly, not on report: **clean under the loader, status FROZEN, 17 hashes
pinned and verified, all 12 mandate-§21 fields**, `--mutate` **6/6 RED** each, and both correctly
**refusing `--for-extraction`** — PR-058 with 10 refusals, PR-059 with 9 — behind their blocking
checklists and `analyzer_exists: false`. Every bank/pool/split hash copied verbatim from `PR-048`;
no hash invented.

**PHASE 10** (mandate §13) does **not** preregister the naive probe at the `bomb` token, which
trivially reads lexical identity. It is a 2x2 already present in the bank: cell **E** (benign demos
remapping the literal ` bomb`) is the symmetric arm, cell **C** the reference codeword-row arm, cell
**B** the matched specificity control — and `target_surface_row_only` implements both halves in one
code path because `target_surface` holds the codeword in A/C and the concept in B/E.

**PHASE 11** (mandate §14) runs on the concept-free `semantic_one_word` channel and on **mapped
regions, never raw last-K**. Two things declared now rather than discovered mid-run: mandate §14.1's
**scope B is unconstructible** (`neutral_content` = **0 tokens in 6900/6900** prompts), and scope A
is exactly `query_last_k_rows` K=5 — so **the first five rungs of any last-K ladder on this template
are pure chat scaffold**, which is mandate §12's warning confirmed quantitatively on our own token
map. `dcs_kladder_analysis.py` is **not** reusable (frozen to PR-032's rung set and `EXPECT_N=380`);
it is a template whose half-of-reference rule PR-059 inherits.

Biggest interpretability risk in each, preregistered rather than discovered: **PHASE 10**'s cell-B/E
query names the concept by construction, so `logp_concept` sits at a ceiling cell C does not have —
mitigated by differencing cell B and by the copy account and the mechanism account predicting
**opposite signs**, declared in advance. **PHASE 11**'s concept-free channel is only weakly engaged
(median `option_mass` 0.1138), so a knockout can move an ordering inside a residual while the output
word never changes; the tempting escape to the display channel is *exactly* the leakage the phase
exists to remove and is forbidden.

## DCS-C-120 — a stale prose note in a FROZEN config, and why it changed nothing
*2026-09-07* — documentation-only, verified rather than assumed

`configs/dcs_ts_pr048.json` `_exclusion_note` reads *"70 train domains are ASSIGNED; **68** are
ANALYSED"* and names only two exclusions (`restaurant_kitchen`, `subway_station`). `school_campus`
was added later, so the correct figure is **67**.

**No result is affected, and I checked rather than assumed it.** The analyzer binds
`population.preregistered_exclusions`, which carries all **three** entries each with a boolean
`whole_population: true`, and refuses any exclusion that fails to declare that boolean. The prose
note is read by **no code path**.

Worth recording as a positive: this is the `C-086` defence working exactly as designed. The lesson
then was that selecting on prose is a defect and a structured field is the fix; here the prose drifted
and the structured field did not, and the structured field is what the analyzer reads. The stale note
should be corrected the next time this config is legitimately reopened — it is FROZEN and was not
edited for this.

---

## DCS-C-121 — the 4-hourly review found that `e9dae21c` did not import
*2026-09-07* — my defect; fixed in `021b20e8` and verified at HEAD

`reports/DCS_TS_PHASE9_INSTRUMENT_REVIEW.md`. Verdict on the committed instrument: **NO — not fit
to run PHASE 9 as committed.**

**F1.** The Q9–Q13 work touched **four** files; I committed three.
`doublespeak_causality/pair_common.py` — 354 insertions carrying `hook_stats_dict`,
`project_out_liveness_violations`, `DisabledHookBridge` and `_resolve_layer` — was left
uncommitted. At HEAD those symbols did not exist, and `score_behavior.py:1432` passes `stats=` to
`AllPositionProjectOut` **unconditionally** (the guard selects `st=None`, but the *kwarg* is still
passed) against a committed signature with no such parameter — so **every pre-existing
`project_out` caller raised `TypeError`**. In a shared tree a broken HEAD is other people's problem.

**How I caused it.** I commit path-limited, which is the rule here and which protected three
concurrent writers today. But I built every pathspec from a `git status` filtered to
`external_md/ reports/ scripts/ src/boombness/ configs/`, and this file lives in
`doublespeak_causality/` — a directory that filter never covered. It was invisible to every check I
ran, *including the checks I ran specifically to see what was outstanding*. The scoped status was
the instrument and it could not see the thing it existed to find: the matcher/scope class, this time
in my own process. I also had the evidence and missed it — the agent reported four modified files
and three appeared.

**The trap worth naming.** Self-test 73/0, mutate 38/38 RED, and "84/84 hook constructions and
300/300 applications bit-identical" all certified a **working-tree** state that no commit recorded.
Every one was true when run and none described HEAD. The review found this **only** because it tested
at a clean detached worktree.

**Verified after the fix, not assumed.** At a detached worktree at `021b20e8`: all four symbols
present, `AllPositionProjectOut` accepts `stats=`. The analyzer self-test there reads 68 checks /
1 failed rather than 73/0 — chased, not waved through: the single failure is `prereg_loads` with
`n=0`, because a detached worktree has no prompt banks (24 files, **1.3 GB**, untracked for size —
tracked banks are ~4.6 MB). Artifact absence, not a code defect. Recorded as a reproducibility fact:
the pinned population lives only on this filesystem, protected by `bank_file_sha16` and regenerable
from the generator scripts.

**F2 confirms `C-117` independently and makes it worse.** Fed **real** producer records that
`hook_stats_dict` itself calls CLEAN, `liveness_gate` returns `live=False` and
`orthogonal_residual_gate` returns `ok=False, max_abs=nan` while asserting *"the orthogonal
component was NOT preserved; H2b is VOID"* — when the truth is the field was never recorded. Two
liveness schemas exist and the one written is not the one read.

**F3.** `rel_end` is persisted as the **absolute** index: for `--pr057-edit-positions=-3`, rows of
length 10 and 17 record `rel_end=7` and `14`, so `pair_common`'s own documented invariant
`resolved_absolute_index == seq_len + rel_end` is false on every row while liveness reports clean —
which reads as evidence of exactly the bug class the field exists to detect.

**Five attack lines returned NO FINDING**, which is a real result: Q10 is genuinely additive (one
fit, no RNG consumption, export after the permutation); Q9 leaves the one-pair assertion intact and
**R-116 stands**; Q13's alias reaches both control families and the gap dose; S1 cannot degrade to
all-position; the layer convention agrees on read, write and probe-fit sides. The "4 pre-existing
failures" claim did not reproduce as stated (the report records no pytest invocation), but the
failures **are** genuinely pre-existing and unrelated — every failing family also fails at the clean
commit and none touches the instrument files.

## DCS-R-122 — PHASE 10's analyzer exists, and PR058-D1 is resolved by moving the CODE
*2026-09-07* — `scripts/dcs_ts_pr058_symmetry.py`, `reports/DCS_TS_PR058_ANALYZER.md`

Built to PR-057's shape: every gate through `Prereg.require()`, domain-level permutation as the only
permutation in the code path, every p through `fmt_p` beside its floor, binding on `cell` and
refusing `condition` *before* the bind, exclusions from the boolean `whole_population`, installation
as a stratifier with a separate refusal if it is ever used as an exclusion, and explicit CANNOT
ANSWER / kill / VOID branches.

The phase's largest interpretability risk is handled **structurally rather than in prose**:
`PairedDelta` cannot be constructed without a `BaselineDistribution`, and `render_delta()` refuses
until the baseline has actually been rendered — so a delta cannot be printed without its baseline.
`ceiling_gate()` differences the cell-B/E ceiling out via cell B; `copy_vs_mechanism()` scores the
two accounts' **opposite-sign** predictions.

Notable: `source_gate_literal_audit()` re-reads the analyzer's own source and fails if a declared
gate value appears as a numeric literal. **It fired during development** — three synthetic test
values happened to equal 0.5, the declared MDE and installation cut — and the file was changed, not
the audit.

Observed: **`--self-test` 55/0**, **`--mutate` 52/52 RED**, refuses with no arm data (rc=1, naming
the outstanding blockers, never an empty result), and cells E/B/C each bind 1130 rows / 113 domains /
67-23-23 on both bomb banks — confirming the config's arithmetic independently.

**PR058-D1 resolved by renaming the file**, not by amending the frozen field: the config declares
`scripts/dcs_ts_pr058_symmetry.py` and the code moved to it. The config is FROZEN; the code is not.

Two checks had to be repaired in the process, and the reason is worth keeping:

- the self-test asserted `match is False` — it had encoded **the conflict itself** as an invariant,
  so it failed exactly when the defect was fixed. A check that hardcodes the current defect state
  fails when the defect is repaired, which is the opposite of what a check is for. It now asserts
  the gate's *behaviour*: that its verdict matches the filesystem either way.
- mutation **M47** fired only because the paths genuinely disagreed, so resolving D1 made it
  **unreachable** and it silently went GREEN (52/52 → 51/52). An unreachable refusal is not a guard —
  this repo says so in `dcs_ts_prereg.py` in those words. M47 now injects the mismatch into a copy of
  the preregistration, so the refusal path stays exercised whatever this file is called. Back to
  **52/52**.

Still open on PR-058, none closable on CPU: T1, T2, T4, T6, T10 (GPU/tokenizer), T3 (code path
exists, needs T2's rows), T9 (the independent verifier — deliberately not written by the same
session, since one sharing these assumptions is not independent). `analyzer_exists` remains `false`
in the frozen config, so the loader still refuses `--for-extraction` with 10 refusals; flipping it is
the config owner's edit.

**PR058-D2**, recorded not papered over: the ceiling rule — the design's own primary defence against
this phase's largest risk — has **no numeric criterion**. "p90 at the top of the scored range" is
unevaluable because no scored range for `semantic_logodds` is pinned anywhere and log-odds are
unbounded a priori. `ceiling_gate()` refuses unless the producing arm persists a `scored_range`; it
does **not** invent a cut. **PR058-D3**: `read_site.position_NOT_USED` is named `codeword_last`, but
in cells B/E the refused site is the *concept* token — a producer labelling that read
`target_surface_last` would slip past a name-keyed refusal, so the gate also refuses every position
that is not the single preregistered downstream site.

---

## DCS-R-124 — C-117, F3 and C-119 are closed; PHASE 9's three GPU blockers clear
*2026-09-07*

**C-117 / F2 — the two liveness schemas are reconciled, with ownership decided rather than patched.**
`n_cells_edited_expected` and `orthogonal_residual_delta_l2` are now the **producer's**: expected is
counted at the top of each forward from the tensor the hook was *handed*, **before** the write, and
realised from the slice actually written — so `realised == expected` is a genuine bind and not
`0 == 0`. The orthogonal residual can only be measured where `h_pre`, `h_post` and `d` all live,
which is the hook.

Missing-versus-zero is the **consumer's**, and this is the part that matters: a new
`NotMeasured(Refusal)` makes an **absent** field raise, while a **measured** zero still FAILS. The
bug was a defaulting `.get` turning a field that was never recorded into a scientific verdict —
`orthogonal_residual_gate` asserting *"the orthogonal component was NOT preserved; H2b is VOID"*
with `max_abs = nan`. It was **not** fixed by making the gate lenient; a dead hook still cannot pass
as a clean null. `hook_stats_dict` now initialises both measured floats to **`None`, not `0.0`** —
a `0.0` default for the orthogonal residual *is* the failing verdict handed to a hook that never
computed it.

The runner also no longer sets `expected := n_destination_rows`, which would have made the identity
true by construction — the same defect one layer up.

**F3 — `rel_end` was persisted as the absolute index; fixed and asserted at three points.**
`SinglePositionProjectOut.__init__` (per row, earliest), `make_intervention`, and
`project_out_liveness_violations` over the persisted record. Replayed through the real
`make_intervention`: `rel_end` is now constant **−3** across rows (was 7 and 14) while the absolute
index correctly varies 7/14/20, `n_distinct_absolute_indices = 3`, violations CLEAN.

A design correction inside the fix, which I would have got wrong: the invariant is
`resolved_absolute_index == seq_len_at_resolution + rel_end`, **not** `seq_len_last + rel_end`. The
hook also fires on the readout's variant forwards, whose lengths differ, and re-resolving there
would *move the edit*.

**C-119 — and a correction to my own account of it.** I recorded, in this log and in two commit
messages, that control C5's `alpha = 0` was **preregistered**. That is **wrong**. The frozen
`controls.arms[C5]` carries only id/name/rule/blocking and preregisters **no alpha at all**; the
`0.0` was a literal in the *unfrozen* `build_arm_manifest`. So this was never "interpreting a frozen
field" — it was an ordinary code defect, and the responsibility is the code's, not the
preregistration's. The distinction matters because "the frozen config says something unrunnable" and
"our code invented a value" are different failures with different fixes.

C5 now runs the **live arm's alpha (1.0) with the write discarded**: the bridge's dose to the model
is zero because nothing is *written*, not because alpha is. At `alpha = 0` the projection is an
identity, so the bridge would have passed with a garbage direction on the wrong layer — certifying
nothing, exactly as suspected, but for a reason I had mislocated. `alpha = 0` is retained as a
tripwire and `build_argv`'s silent `arm.alpha or 1.0` fallback is removed.

**F6 and F9 fixed too.** F6: `min_projection_removed_l2` — the minimum over forwards, so a
*partially* dead hook can no longer pass on the last forward alone. F9: the consumer's `cos == 1.0`
gate is replaced by the producer's scale-free relative-magnitude rule (stricter and
dose-independent), with cosine still required to be recorded. The added fired-count identity is
stated honestly in the report as a **tripwire** rather than a check, since it holds by construction
in today's hooks.

**Observed, all on the final file state:**

| harness | before | now |
|---|---|---|
| `dcs_ts_pr057_causal.py --self-test` | 73 / 0 | **77 / 0** |
| `dcs_ts_pr057_causal.py --mutate` | 38/38 RED | **52/52 RED** |
| `pr057_run_causal.py --self-test` | 49 / 0 | **50 / 0** |
| `pr057_run_causal.py --mutate` | 26/26 RED | **28/28 RED** |
| `--plan --split test` | 26 constructible | **28 constructible** (the two C5 bridges) |

The reviewer's exact F2 reproduction now returns `live = True` (expected 3 = realised 3) and
`ok = True, n_violations 0/3, max_abs = 1.82e-06`, against the previous `live=False`, `ok=False`,
`max_abs=nan`. A missing `n_cells_edited_expected` raises `NotMeasured`; a measured 0 still gives
`live=False`. Tests completed rather than cancelled: 43 passed (5 hook files) and 237 passed
(11 readout/intervention files).

**Still blocking Q1, and named rather than glossed:** `C-113`; `C-118` (`--emit-probe` refused, no
`FROZEN_PROBE` block on disk); and **26 of 54 arms still unbuildable** — including **C4's `add` mode,
which remains uninstrumented (`pc.AllPositionAdd` receives no `stats=`)**. That is now *the one
remaining place where a dead hook could score as a clean null*, and it is the reason C4 must not be
quietly reinstated.

---

## DCS-R-125 — PHASE 11's analyzer, and mandate §12's warning confirmed on our own tokens
*2026-09-07* — `scripts/dcs_ts_pr059_localisation.py`, `reports/DCS_TS_PR059_ANALYZER.md`

Written at **exactly** the path `artifacts.analyzer` declares, so the PR058-D1 rename defect is
designed out rather than repeated. The identity gate is kept anyway, with mutation M40 injecting a
mismatch into a *copy* of the prereg so the refusal stays reachable — the M47 lesson applied
prospectively.

Observed: **`--self-test` 92/92, 0 failed**; **`--mutate` 80/80 RED**, every message read to confirm
each fires for its own intended reason rather than a stray exception; `--verify-token-map`
`ok=true`, 6900/6900, `problems=[]`; the default analysis **REFUSES** with no arm data (rc=1,
"78 arm tags searched, 78 absent", listing the 8 outstanding blockers); source-literal audit clean
on 12 declared gates.

**U4 — both structural claims CONFIRMED, re-derived from the raw `query_roles` arrays rather than
from the design's summary.**

- **Scope A *is* `query_last_k_rows` K=5**: `sorted(query_span)[-5:]` equals S_A's declared set in
  **6900/6900** prompts, and those five rows are `<|eot_id|>`, `<|start_header_id|>`, `assistant`,
  `<|end_header_id|>`, `'\n\n'` — one `chat_scaffold` plus four `response_header`, **zero query
  content**. This is mandate §12's warning ("avoid raw last-K rows when they include unknown chat
  scaffold") confirmed quantitatively on this template: **the first five rungs of any last-K ladder
  here are pure scaffold.**
- **Scope B *is* unconstructible**: `neutral_content` = **0 tokens across all 6900 prompts**
  (`concept_word` likewise 0). S_B enters Holm at p = 1.0 as an absent member rather than being
  silently dropped.

Also confirmed: S_C = `codeword` (` button` 3450 / ` basket` 3450), S_D = 22, S_E = 23 (S_D plus the
codeword row), S_F = ` actually` 6900/6900, S_G = 28.

## DCS-PR059-D1 — the preregistered control is ARITHMETICALLY IMPOSSIBLE for the primary contrast
*2026-09-07* — BLOCKING, needs an amendment, config NOT edited

`dose_matching.per_scope_random_row_control` requires, for **every** scope, an m-row draw from the
query span **excluding the scope's own rows**. The span is **28 rows**. So:

- **S_D** needs 22 rows drawn from a pool of **6**.
- **S_E** needs 23 rows drawn from a pool of **5**.

The control cannot exist for the two largest scopes — and **S_D vs S_E is the phase's declared
primary contrast** (they differ by exactly the codeword row). This is arithmetic, not a shortage of
data, and no amount of GPU time changes it.

The analyzer does the right thing: it **refuses to draw fewer rows and call the result
dose-matched** (mutation M58), omits those control arms from the manifest, and
`assert_scope_has_its_control()` then refuses to render S_D/S_E at all. So PHASE 11 as frozen cannot
report its own primary contrast.

Resolving this is a **design decision that changes the preregistration**, and it is recorded rather
than taken quietly. The options, with what each costs:
  1. draw the control rows from the **demo block** instead of the query span — rows are plentiful,
     but it changes *what the control controls for*;
  2. drop "excluding own rows" and allow overlap — then it is not a control;
  3. accept that S_D/S_E have **no** random-row control and demote them from primary, relying on the
     other declared controls;
  4. redefine the primary contrast onto a smaller scope pair.

None is taken here. PHASE 11 has seven other blocking items outstanding and is not runnable
regardless, so nothing is lost by leaving this to an explicit amendment (a new preregistration
superseding the control rule) rather than an edit to a frozen file.

**U3 is NOT closable, and the reason is a population fact.** *Zero* knockout runs on the
concept-free channel exist on any of the six preregistered `ts116m` banks. The nearest usable rows
are the `dcssow_*` family — right channel, right cell, right dose, matched baseline — but **6
domains on `button_bomb`, only one of which (`game_manual`) is a ts116 validation domain**. An SD
over n=1 does not exist, so the between-domain SD the power calculation needs cannot be measured
from what is on disk. Recorded descriptively and entered nowhere.

⚠ **Two warnings that carry forward.** From that off-population bank, the **K=5-shaped arm MOVES**
(Δ = −0.87) — and a scaffold-only scope moving the readout is the frozen file's **third kill
condition**. It is off-population and a different template, so it is a warning and not a result; but
it is exactly the thing U8's smoke run must check before anything larger is submitted. Second, at
the descriptive SD of 1.279 the 0.5-nat effect has power 0.985 / 0.884 / **0.434** at n = 113 / 67 /
23 — so a test-split-only reading of PHASE 11 would be badly underpowered.

**Closable now: U4, U5, U6.** **U1 and U2 are half-closed** — the declared-offset selector and the
seeded random-row draw exist, are tested and mutation-covered in the analyzer, but their
producer-side halves live in `score_behavior.py` and `dcs_extract_under_ko.py` and remain
BLOCKING. **U3 not closable.** `analyzer_exists` stays `false` in the frozen config, so the loader
still refuses `--for-extraction` with 9 refusals.

---

## DCS-R-126 / C-122 — the last two code blockers close, and two more real bugs fell out
*2026-09-08*

**C-122 (C4's `add` mode was uninstrumented) — closed, and it was the right thing to prioritise.**
C4 is the equal-magnitude orthogonal control: the arm whose whole job is to separate *"this
direction matters"* from *"this much perturbation at this site matters"*. Running dead, it would
have produced exactly the **"the control did not move the readout"** result that a positive H2a
wants to see — a false confirmation in the most sceptical arm. It is now instrumented to the same
standard `project_out` meets under Appendix A's ownership split: expected counted **before** the
write, realised from the slice written, missing raises `NotMeasured`, measured zero fails, and the
new dose fields initialise to `None` rather than `0.0`.

**Two further defects surfaced only because someone tried to build the arm:**

- **C4 × S1 would have been an all-position edit under an S1 label.** There was no
  single-position additive form at all; `SinglePositionAdd` / `make_single_position_add_hook` now
  provide one under the same `pos` / `rel_end` / `seq_len_at_resolution` contract.
- **`build_argv` hard-coded `"project_out"`**, so the orthogonal control **would have been launched
  as a projection** — C4 would have run the very intervention it exists to be different from.

**Gap units verified both ways**, at the call site where this project has already been bitten twice:
`alpha=1 × gap 2.5 → effective magnitude 2.500000`, realised per-cell 2.5000; a bare alpha (absolute
magnitude wearing a gap-unit label) is **refused at construction** and is separately convictable
from the persisted record alone.

**C-118 — both halves closed, and the stated reason for one of them was half wrong.**

- **(b) the frozen probe now exists on disk.** A new `--export-frozen-probe-only` reads the frozen
  selection (L9, C=0.01) rather than re-selecting, loads only that layer, re-fits the observed pass,
  and **refuses unless the re-fit reproduces the published number bit-for-bit**. It reproduced
  exactly: `0.939855072463768 == 0.939855072463768`, **0 per-domain disagreements**, probe sha
  `c54bd397…`, self-verified 0/1380. The ~7.8-hour permutation was **not** re-run and the TEST split
  was not re-read. Verified additive on disk: `FROZEN_PROBE` added, `permutation` and
  `SELECTION_TRACE` intact, `observed_domain_mean_accuracy` unchanged. Review findings **F4 and F5**
  close with it.
- **(a) O1 IS capturable.** The recorded blocker said `score_behavior` exposes no per-row callback,
  so attribution would be order-based guesswork. Half of that was wrong: `make_intervention` is
  already constructed **inside the row loop** — it must be, because the edit site is end-relative —
  and the liveness writer already stamps `prompt_id`/`domain` from there, so **attribution is by
  construction**. The real half (many forwards per row, at different lengths) is closed by pinning
  the read to the absolute index resolved against that row's prompt, emitting one record per row per
  layer, and **refusing** a row whose forwards disagree at that index rather than averaging.

**Observed, on the final tree:**

| harness | before | now |
|---|---|---|
| `dcs_ts_pr057_causal.py --self-test` | 77/0 | **86 / 0** |
| `dcs_ts_pr057_causal.py --mutate` | 52/52 RED | **64/64 RED** |
| `pr057_run_causal.py --self-test` | 50/0 | **53 / 0** |
| `pr057_run_causal.py --mutate` | 28/28 RED | **28/28 RED** |
| `dcs_ts_pr048_analysis.py --selftest` | 16/16 | **20/20** |
| constructible arms | 28 | **30 of 54** |

Both C4 arms are now constructible. The remaining 24 are refused **by name**: 16 H1 + 2 C7
(`patch`, and the empty R-116 donor population), 4 H2b (`component_replace`), 2 C2 (no shuffled-label
direction). Tests run to completion: **43 passed** (5 hook files) and **248 passed** (12
intervention/readout files); the whole-root suite does not collect at this root and one background
run was OOM-killed at load ~130 — reported as killed, **not** as a pass.

Two guards were **re-pointed rather than deleted** when the fix made them unreachable — `M25` now
targets an absent artifact, and the `unbuildable_add` self-test was **inverted**. That is the M47
lesson applied twice without being asked: a guard made vacuous by a fix must be re-aimed, not
removed.

**ID collision, recorded not silent.** This work arrived labelled `C-120`, which the log had already
given to the stale `_exclusion_note` finding. Renumbered to **C-122** across the code, the review
appendix and the `DEFECT_*` constants, and the harnesses re-run afterwards to prove the rename broke
nothing: **86/0, 53/0, 20/20, 30 constructible**. That re-run is not ceremony — a rename broke a
hardcoded check on PR-058 earlier today.

**What still blocks Q1:** nothing from these two. Remaining is (i) `C-113`, documentation-only;
(ii) the **`score_behavior` half of the O1 capture has never run against a model** — flags, probe
load, sha pin, hook and argv are all CPU-verified, but the in-loop wiring needs the **Q7 smoke
stage** before any O1 number is reported, which does not block Q1 since Q1's outcome is O2; and
(iii) a `--dry-run` on the shared filesystem immediately before submitting.

---

## DCS-R-127 — PHASE 9 reaches the GPU: Q1 PROCEEDs and Q7 smoke is CLOSED
*2026-09-08*

**Q1 (job 867233), the validation power run.** 2 arms, 460 rows, 3.7 min compute, `COMPLETED 0:0`.
Verdict **`PROCEED`**. 230 rows / 230 liveness records / **230 hook firings, 0 violations** per arm.
This is the first time the intervention path has run against a model at all.

**The verdict is soundly earned and the SD was MEASURED, not assumed** — 0.042008 nats between
domains over the 23 validation domains, independently re-derived from the raw `results.jsonl`
paired against the untouched PHASE 7 baselines and byte-matching `DONE.json`. Zero test leakage:
the 930 dropped rows are exactly train 700 + test 230.

⚠ **Publish the MDE, not the power.** `power_at_declared_mde = 1.0` is saturated and carries no
information — the declared 0.5-nat effect is ~14x the arm-averaged validation delta. The informative
figure is **MDE = 0.0257 nats at 80% power, n = 23, measured SD 0.0420**.

**What is now PROVEN on GPU**, with numbers rather than assertions: `rel_end` constant at **−10 on
all 460** rows while `resolved_absolute_index` takes **57 distinct values spanning 191–253** (`F3`
is genuinely fixed, not merely patched); the edited index equals `codeword_last_indices[-1]` on
**460/460** — independent corroboration that the edit hit the intended token, and stronger evidence
than the expected/realised bind; `projection_removed_l2` non-zero on all 460; probe **1840 records
per arm = 230 x 8 layers, one per (prompt_id, layer)**, attributed from the row loop rather than by
arrival order; and the layer-9 read is empirically **post**-edit.

**What is NOT proven, and the first is large: no S2 arm has ever run on a GPU.** All 15 S2 arms in
H2 edit 8 layers at every position; their cost and liveness behaviour are both untested. Also
unexercised: the many-forwards disagreement guard (`n_forward_calls == 1` throughout, and H2 is also
`--no-generate`); `min_projection_removed_l2` is vacuous with one forward per row and must not be
cited as an active partial-dead-hook guard; and there is **no un-intervened layer-9 arm**, so every
L9 posterior reported so far is post-edit.

**Q7 smoke CLOSED (job 868758).** `h2a_s1_projout_button` 40 rows / **40 hook firings**;
`c5_disabled_bridge_s1` 40 rows / **0 hook firings** — correct, a disabled bridge edits nothing.

## DCS-C-123 / C-124 — two defects of mine, both caught by guards doing their job
*2026-09-08*

**`C-123` — the smoke stage contradicted itself.** It emitted `--expect-n 670` beside `--limit 40`:
the first says "score the whole bound population", the second truncates it to 40. `score_behavior`'s
row-count guard refused — *"population is 40 rows, --expect-n says 670. A silently-shrunken sample
is how R-18 happened."* **The guard was right and my runner was wrong**: `expect_rows` was clamped
for the runner's own bookkeeping and the *unclamped* count was put into the argv. Two variables that
must agree, clamped in one place and not the other.

Fixed by clamping **once**, above the ctx, so the argv and the runner's expectation cannot drift;
the same defect was present in the `--plan` path, which is worse in one way — `--plan` is what a
human reads to decide what to submit, so it printed a command that would refuse. New
`assert_expect_n_agrees_with_limit()` refuses in the runner **before** submission rather than on a
GPU after a queue wait, with mutations **M65/M66** covering both directions (shrunken *and* widened).

**`C-124` — a successful run discarded by a stale verdict.** Job 868702 ran **both** smoke arms to
completion and was refused at the very last step, because job 868569 — dead 13 seconds in on
`C-123`, having completed **zero** arms — had already written `ABORTED.json`. "A stage has ONE
verdict" is the right rule; enforcing it **only at the end** is not.

`assert_stage_has_no_prior_verdict()` now refuses at the **start** of a stage. The remedy is
deliberately **not** automatic: a terminal record is evidence, and silently overwriting one is how a
failed run gets quietly reported as a success. The stale file was **archived with provenance**
(`ABORTED.868569.superseded.json` + `SUPERSEDED_NOTE.md`), never deleted, and the stage's real
verdict still came from the runner — 868758 resumed, skipped both completed arms (0 model loads,
0.6 min) and wrote `DONE.json`.

## DCS-C-125 — my SLURM diagnosis was wrong, and the 30-minute rule needs a caveat
*2026-09-08* — correcting a claim I made confidently

I reported that job 867233's 42-minute pend was caused by requesting `--time=06:00:00` for a
4-minute job, and that the fix was a shorter walltime. **The evidence says otherwise.**

Across the entire pend window **zero jobs started on any of the six L40S nodes**; all 48 GPUs were
held; the holding jobs carried TimeLimits of 18h (x23), 24h (x10), 5d (x6), 3d (x1) — **our 6h was
the shortest in the queue**; and 867233 started **one second** after 865619 released. That is
capacity exhaustion, not request shape. A short `--time` wins only when a backfill *gap* exists.

Two further corrections. **There is no L40S anywhere outside those six nodes** (`sinfo` verified), so
"widen the nodelist" — the standing house fix — has nothing to widen to; and widening means changing
GPU model, which control C5 forbids outright, since `disabled_bridge_gate` demands a byte-identical
greedy hash against an L40S-produced baseline. **And fair-share was not the blocker**: 867233 held
priority 100001114 and beat five jobs submitted 21 minutes earlier at 100001042, with fairshare
contributing ~1131 of ~100,001,131. The standing belief that "the real blocker is always fair-share"
is **false for this event**.

**The 30-minute rule needs one caveat.** Cancelling 867233 at the mark would have surrendered a
top-of-queue position, and the GPU freed at 04:30:27 would have gone to another user. Refined rule,
now implemented in the monitor: `Reason=Priority` → cancel and resubmit with a different shape;
`Reason=Resources` **with a planned `START_TIME` inside ~30 min** → do **not** cancel, and log the
deviation with the `START_TIME` that justified it. Requesting a realistic walltime remains correct —
it is free upside — it simply is not the lever when every GPU is held.

`--open-mode=append` is now set on every submission, and it is **not** cosmetic: `JobFileAppend=0`
with killable's `PreemptMode=REQUEUE` and `GraceTime=0` means a requeue **truncates** the log and
destroys the previous attempt's evidence.

---

## DCS-C-126 — I reported "Q7 smoke CLOSED". It is a SUBSTITUTION, not a satisfaction.
*2026-09-08* — correcting `R-127` and commit `6d2ecae3`

Checklist item Q7 reads, verbatim:

> *smoke run: **H1 at S1** on a handful of TRAIN domains, confirming hook liveness, **the self-patch
> identity control**, and a non-zero measured edit magnitude, BEFORE the full submission*

What the smoke stage actually ran was **`h2a_s1_projout_button` + `c5_disabled_bridge_s1`**. Not H1,
and not the self-patch identity control. And since H1 is unbuildable by construction, **the
self-patch control cannot be exercised at all** on this bank — it is CANNOT ANSWER BY CONSTRUCTION,
not merely "not yet done".

So the smoke **stage** completed and proved real things — 40/40 hook firings, 160/160 cells, the C5
bridge firing 0 times exactly as a disabled bridge should. **Checklist item Q7 is not satisfied by
it.** I wrote "Q7 smoke CLOSED" in `R-127`, in the summary, and in commit `6d2ecae3`'s message. That
was wrong, and it is the kind of wrong this project cares about most: a declared item ticked because
*something* ran, rather than because *the declared thing* ran. Q7 must be **amended** — with the
substitution and its reason recorded — never ticked.

Also confirmed: `smoke_train/DONE.json` records **no SLURM job id** (`job id recorded? False`), and
the arm-level `RUNMETA.json` carries `slurm_job_id 868702` while the terminal record was written by
a later invocation. So the terminal record cannot be traced to the job that produced it. Recorded as
**A15**.

## DCS-R-128 — PR-060, the amendment, and the two irreversible answers
*2026-09-08* — `configs/dcs_ts_pr060_phase9_amendment.json`, `reports/DCS_TS_PR060_AMENDMENT.md`

Verified by me, not on report: **clean under the loader — status FROZEN, 52 hashes pinned and
verified, all 12 mandate-§21 fields**; `--mutate` **6/6 RED**; and it still **refuses
`--for-extraction` with 9 refusals**, so the NO-GO is enforced by the loader rather than asserted in
prose. It names the parent it amends (`DCS-PR-057`, `amends_file_sha16 7c88346ee375baaf`) and lists
exactly which fields it supersedes — the frozen parent is never edited.

**Two questions answered before any test read, which is the whole point of asking them now:**

- **The Holm family survives absent members.** `m` stays **6**; H1×S1/S2 and H2b×S1/S2 enter at
  **p = 1.0** as structurally absent rather than breaking the family, so H2a faces thresholds
  0.008333 and 0.01. **The design is NOT void** despite 6 of 36 arms being unbuildable — this was
  the single largest risk to the confirmatory run and it is retired.
- **O1's baseline is the C5 disabled-hook bridge**, paired by `prompt_id`. But that forces a new
  problem (**A12**): both C5 arms bind `..._button_bomb.jsonl`, and the analyzer hardcodes
  `codeword='button'`, so **there is no basket reference**. An arm cannot be added after TEST is
  read, so this must be resolved first.

**Closed on evidence run or read:** A0/Q0 (job 865335, 6/6 banks `gate=PASS`, `missing_tags=[]`),
A1/Q1 (SD 0.04200821142171075, MDE 0.025678627181435994, PROCEED), A2/Q2 (fit = 67 TRAIN domains,
VERIFY 28/28, MUTATIONS 22/22, sha recorded in 4/4 arm gates), A5/Q5 (`--mutate` 64/64, **all seven
named mutations RED**), A6/Q6 (`--self-test` 86/0 including the five `c122_*`; M54/55/56/58/61 RED,
with the residual gap — no GPU round-trip of a live C4 arm — recorded rather than glossed).

**Left open deliberately, and this is the honest part:** A3 (the donor is genuinely absent —
`score_behavior.py:1811` still `choices=("clean","self")`), **A4 (`analyse()` returns at
`:3057-3059` with no verdict path)**, A7b (self-patch, CANNOT ANSWER BY CONSTRUCTION), A8 (PR-056
status **could not be determined**), and new blockers A9 (launch order), A10 (Holm-with-absent and
`arms_present` scoping), A11/A12/A13 (O1 estimator, the basket reference, `--emit-probe`), A14
(a stage-aware checklist gate), A15 (job id absent from terminal records).

**Verdict: NO-GO for H2, and the wording matters — *the design is not void, the instrument is not
ready*.** Those are different diagnoses with different remedies, and the second is fixable work
rather than a dead end.

---

## DCS-R-129 — the analyzer can now return a verdict, and a validation run nearly leaked into a test result
*2026-09-08*

**`A4` closed — this was the one that mattered.** `analyse()` ran to `return 0` after the liveness
gates; `evaluate_success` and `holm` had **no production call site**. A flawless H2 run would have
produced nothing. It now computes O1 and O2 as paired domain-level contrasts, runs the domain
permutation, applies Holm over the declared family with **m pinned at 6** (absent members at
p = 1.0; observed thresholds **0.00833333** and **0.01**), evaluates the four conjuncts
**separately with a PASS/FAIL line each** so a reader sees *which* failed, walks **every** clause of
`primary.void` and `primary.cannot_answer`, and emits one verdict.

Three properties are structural rather than editorial, which is the point:
- `verdict_class` is one of `VOID` / `CANNOT ANSWER` / `NEGATIVE` / `SUPPORTS` / `NOT A CAUSAL
  RESULT`, so **VOID and NEGATIVE cannot collapse into each other**. They mean different things.
- the mandated negative wording is emitted **as a literal, first** — not paraphrased.
- **no null-shaped branch can be emitted without its realised dose**: `format_realised_dose` raises
  `NotMeasured`. The claim table *bans* a bare "not causally used"; the analyzer now makes that ban
  impossible to violate rather than merely discouraged.

An UNEVALUABLE void clause **refuses** the verdict rather than passing it; a clause scoped to an
unbuildable arm is `NOT_APPLICABLE` **plus a stated scope limit**. `arms_present` is scoped to the
stage and to the arms the **runner** re-derived as unbuildable in its own terminal record — never a
list typed into the analyzer, which would drift.

⚠ **A real hole found in passing, and it is the serious kind: the analyzer would have read the Q1
VALIDATION run of `h2a_s1_projout_basket` into a smoke or test analysis.** Validation data entering
a test result silently. Runs are now bound to `<stage>_<split>/` via the recorded exclusion-file
path. Nothing had been published from it — but nothing would have flagged it either.

**`A12` decided rather than fudged.** O1 is scoped to the **development codeword bank** and the
scope is **named in the output**; `o1_contrast` **refuses** an arm/bridge codeword mismatch by name.
The alternative — silently pairing basket rows against a button baseline — is a cross-codeword
comparison wearing a baseline's name, and is worse than an honestly scoped result. Building basket
bridges would have cost GPU without changing any family member, since the corrected members are the
development-codeword arms.

**`A9`** — `assert_stage_order` re-derives h1's constructibility at launch and records
`CANNOT_RUN_BY_CONSTRUCTION` with per-arm reasons. Crucially **no terminal record is written for an
empty stage**: `run_stage`'s refusal is untouched, so the "an empty stage reports success" hole
stays closed. **`A14`** — the stage-aware gate scopes out **exactly one** item from h2 (A3, since
0 of 36 h2 arms use mode `patch`), and only because the runner can re-derive that from the stage's
own arms. **`A13`** `--emit-probe` is now required for h1/h2 and refused before the model loads;
**`A15`** the SLURM job id, node and host are stamped into every terminal record and the manifest,
closing the traceability gap C-126 recorded.

**Observed:** analyzer `--self-test` 86 → **100/0** and `--mutate` 64 → **82/82 RED**; runner
53 → **64/0** and 30 → **37/37 RED**. New mutations include: each conjunct failing alone must not
yield success (M65–M68), VOID reported as NEGATIVE (M69), CANNOT ANSWER as NEGATIVE (M71), an
absent Holm member shrinking `m` or loosening the threshold (M72/M73), and a null printed without
its dose (M75). Tests to completion: 43, 248 and 81 passed.

**Exercised end-to-end on real artifacts** (TRAIN smoke, diagnostic only, no test data): O2 delta
+0.035428, p = 0.254775 [floor 9.999e-05]; O1 delta +0.415496, p = 0.124588, scope = button; dose
`frac_cellmean_spread_removed = 0.1656`, `cell_residual_frac_removed = {'C': 0.0936}`. And the smoke
analysis **correctly refuses a verdict** — there is no C1 control band, so the "identical
control-draw hashes" clause is UNEVALUABLE. The refusal is the instrument working.

---

## DCS-R-130 — the H2 gate opens: dry-run rc=0, and A3 stays open on purpose
*2026-09-08*

Seven checklist items closed **with evidence attached to each**, not as bare booleans: A4 (the
verdict path), A9 (launch order re-derivation), A10 (Holm-with-absent), A11 (O1 as a paired contrast
against the C5 bridge), A12 (the preregistered fallback, taken deliberately), A13 (`--emit-probe`
required for h1/h2), A14 (stage-aware scoping). `artifacts.analyzer_exists` and
`analyzer_verdict_path_present` set true.

**The convention was checked, not assumed.** `configs/dcs_ts_pr048.json` is FROZEN with all five of
its checklist items `done: true` and `analyzer_exists: true` — so in this project the freeze protects
the **design**, and the pre-extraction checklist is the **operational ledger**, flipped as items
complete with evidence. That is how PR-048 reached extraction, and it is what was done here.

**Every number was re-run by me before the gate was opened**, because I over-claimed Q7 earlier the
same day and would not repeat it on the gate that lets TEST be read: analyzer **100 checks / 0
FAILED** and **82/82 mutations RED**; runner **64 / 0** and **37/37 RED**. All four match the agent's
report exactly.

**Two stale pins corrected** in the same edit — the analyzer had drifted from `2c2f80038c905fa1` to
`26ac2c0ac8bd8599` and the runner from `c74d16763a349be4` to `ad4bafa4bd862188` — so the config now
pins the instrument that was actually verified. All 52 hashes re-verify against disk.

**A3 is left OPEN deliberately.** There is genuinely no cross-prompt donor code path
(`score_behavior.py:1811` still `choices=("clean","self")`, both on the same prompt), so it is not
closed and not marked N/A. `dcs_ts_prereg.py --check --for-extraction` still refuses on it — **one
refusal, and it is the right one**. The stage-aware scoping that lets h2 proceed lives in the
**runner**, which re-derives from the stage's own arms that 0 of 36 use mode `patch`; the loader
itself remains fail-closed and stage-blind. The two disagree by design, and that is the safe
direction: the strict gate stays strict.

**`h2 --split test --dry-run` returns rc = 0**: launch order satisfied as
`CANNOT_RUN_BY_CONSTRUCTION` (0 of 18 h1 arms constructible, **no `DONE.json` written for it and
none needed**), 30 arms constructed and validated, model not loaded, nothing written.

**What the confirmatory run still cannot escape, restated so it is not lost at the moment of
submission:** no S2 arm has ever run on a GPU and 15 of the 30 are S2; H1's upper bound is
unbuildable, so a positive H2a has no full-patch control (`A-047`, `arXiv:2311.17030`); the realised
dose is 4.7–19.0%, so a null is weak evidence of non-use and must be published with the dose
attached; and O1 is scoped to the development codeword only.

---

## DCS-R-131 / C-127 — H2 reaches the GPU; the S2 gap costs one arm instead of fifteen
*2026-09-08*

**Job 869332 ran the H2 confirmatory stage.** Arms 1 and 2 (`h2a_s1_projout_{basket,button}`)
completed cleanly — 230 rows, 230 liveness records, **230 hook firings** each. Arm 3
(`h2a_s2_projout_basket`) was the **first all-position S2 arm ever run on a GPU**, the single
largest untested surface named in `R-127`. **It ran fine**: 230 rows, **1840 liveness records**
(230 x 8 layers), 0 violations, 1840 probe records, option-mass median 0.05284 OK.

It was then refused at artifact verification for one field: *"did NOT persist 1 field(s) the frozen
`persist_per_row_and_per_arm` list requires: ['occurrence index of the codeword']"*. The liveness
writer derived that ordinal **only** from `resolved_absolute_index`, which an all-position edit does
not have. The row's `codeword_last_indices` `[174,192,211,230,250]` were **already in the record** —
only the ordinal was missing.

**The kill condition behaved correctly under an unbuildable H1**, which is worth recording because it
is the distinction the phase depends on: it logged `H1_NOT_AVAILABLE` and stated explicitly that this
is **not** read as *"H1 did not move O2"*. Never-ran and ran-and-null stayed distinct under real
conditions.

**The fix, and the semantics are the point.** "Occurrence index of the codeword" is a property of the
**prompt**, not of the edit, so it is now populated for all-position arms too — via one
`occurrence_annotation()` reused by every mode and built on the existing occurrence resolution, and
carried with `occurrence_index_is_prompt_property: true` so an S2 record can never be misread as
having been edited at that site. **`rel_end` and `resolved_absolute_index` STAY null on all-position
arms**, now enforced by two independent checkers plus a new producer refusal — inventing an edit site
would have been far worse than the missing field.

**The field x mode sweep is what made this cheap.** Rather than fixing only the arm that failed, all
19 frozen fields were checked against all five modes. **Both** all-position modes were missing the
ordinal — so `c4_samenorm_orth_s2`, the ten `c1_random_s2_*` draws, `c3_vremap_s2` and
`h2a_s2_projout_button`, **15 of the 30 arms**, would each have died at the same gate, one queue wait
and one partial run at a time.

A second defect of the same class fell out: the "all positions (S2)" note was printed for **every**
record lacking a `rel_end`, including the C5 bridge over a *single*-position hook — and a **live**
single-position record with no site was **silently excused from the end-relative audit**. Now a
refusal.

**`C-127` — and this one is mine, for the third time in two days.** The runner self-test
`a14_analyzer_exists_still_gates` asserted that `"analyzer_exists"` appears in the LIVE config's
blocking list. `R-130` legitimately flipped that flag to true, having built the verdict path — and
the check that verifies the flag blocks **failed because the flag no longer needed to block**. A
check that hardcodes the present state fails exactly when the state is repaired.

This is the same class as PR-058's `identity_gate` self-test and mutation `M47`, both fixed earlier
the same day, and I then committed a third instance myself. Fixed the same way: the check now
**injects `analyzer_exists: false` into a copy** and asserts the gate refuses, so it tests the gate's
*behaviour* and survives the real flag being either value.

**Observed after all fixes:** analyzer `--self-test` **104 / 0** and `--mutate` **85/85 RED**; runner
`--self-test` **70 / 0** and `--mutate` **41/41 RED**; `h2 --split test --dry-run` **rc = 0**, 30 arms.
Repo tests 676 passed / 0 failed across 26 files, run to completion.

**Resume, not restart.** Re-verified against symlink copies so no artifact was overwritten: both S1
arms of job 869332 **pass unchanged**. Arm 3 re-runs because the fix is in the producer; arms 1 and 2
do not.

---

## DCS-R-132 — the H2 confirmatory run COMPLETES; two analyzer defects found before the verdict
*2026-09-08* — job 869523

**The run:** 30 arms, **6,900 rows**, 54.3 min, 1 model load, `COMPLETED 0:0`, `DONE.json` written.
The analyzer loads all 30 with **0 check failures**: every liveness gate PASSED including the
1840-record all-position arms; every S1 index audit passed with **54 distinct absolute indices over
230 records** (end-relative addressing proven under real conditions, not asserted); the C5 bridge
recorded 1840 liveness records and **0 hook firings**. The kill condition logged `H1_NOT_AVAILABLE`
and stated explicitly that this is **not** read as "H1 did not move O2".

Then the analyzer **refused a verdict**, and the refusal was correct twice over.

**I proposed the wrong fix and was overruled by the evidence.** My instinct was to build the missing
basket C5 bridge — "make the measurement rather than argue it away". That would have been wrong:
building it forces the **frozen** amendment to change three ways (`arm_inventory_observed` pins
`n_arms 54` / `n_constructible_today 30` **as fact**; A12's `closed_evidence` "Basket bridges were
NOT built" becomes false; and `design_answers.o1_baseline.deterministic_fallback`'s antecedent flips
**after** the confirmatory run executed). That is retroactively editing a pre-outcome choice.

And the design never wanted a per-bank bridge. The decisive evidence is a contrast inside
`nulls_required`: **I-N3 says "hook liveness, EVERY LIVE ARM"; I-N1 says only "disabled-hook bridge",
with no quantifier.** Where this design wants per-arm replication it says so. `population.codewords`
is `{"development": "button", "external_confirmation": "basket"}`, `multiplicity` puts
"lexical transfer button→basket" in **SECONDARY**, and frozen item A12 had already chosen the
button-only fallback explicitly.

**Defect 1 — the analyzer refused the whole run on behalf of arms that can make no claim.** The
basket arms are non-family replication arms, already `REPORTED O2-ONLY` and already CANNOT ANSWER.
`_absent_null_status()` now switches on the arm's bank **and nothing else**: development codeword →
`UNEVALUABLE` and **still refuses** (the anti-fiat guard, proven by mutations M86/M86b/M86c going
RED); any other bank → `VOID_CLAUSE_NA` with the I-N2 wording already used twice in this file
("a STATED SCOPE LIMIT, not a passed control"). Nothing is upgraded.

A consequence not anticipated in the analysis: fixing the C1 defect below leaves the basket arms with
**no** C1 draws, which would have made the "identical control-draw hashes" clause UNEVALUABLE and
refused for the same wrong reason. That clause takes the same switch — but **only** behind an
explicit `control_scope_limited` flag, true solely when no C1 arm is *declared* on that bank. Any
other absent band still refuses. **A scope limit and a broken measurement do not share a code path.**

**Defect 2 — the decisive control was silently computed ACROSS codeword banks. This is the serious
one.** `c1_draws` filtered on scope and hypothesis only; every C1 arm is declared on `button`, while
a basket arm's `base` is the **basket** baseline. The two banks share **22272/22272 identical
`prompt_id`s**, so `paired_outcome`'s zero-overlap guard and the domain guard **both pass** — the
mismatch was invisible to every existing check. C1 is the norm-matched random control: the null the
primary claim rests on.

Fixed the way this codebase already fixes the class: `c1_draws` now requires `codeword` equality (as
`_bridge_for()` always did) and `control_c1_report` **raises by name** on a mismatch *before* pairing
anything, modelled on `o1_contrast`'s M79. Mutation **M88** is the sharp one — it asserts the premise
that identical `prompt_id`s and domains pair cleanly, demonstrating that M80/M81/M82 **cannot** see
this defect.

**Recorded as a weakening, not a gain:** before this fix the basket arms reported a C1 computed
against the other bank. That evidence is now correctly **gone**, both basket arms are left with no C1
control, and conjunct 3 of the success rule stays FALSE for them. Stated in three places a reader and
a program both see: `C1_scope_note`, the `NOT_APPLICABLE` clause detail, and the conjunct itself.

**Observed:** analyzer `--self-test` 104 → **111 / 0** and `--mutate` 85 → **90/90 RED**; runner
**70 / 0** and **41/41 RED**; h2/test **30 arms loaded, 0 check failures**; 37 nearest-neighbour tests
passed. **No outcome value, p-value or verdict was printed, read or reported** during either fix —
the analyzer was corrected without anyone seeing what it will say.

---

## DCS-R-133 — PHASE 10's CPU blockers close; `concept_word` is NON-EMPTY on cells B/E
*2026-09-08*

Loader refusals on `configs/dcs_ts_pr058_phase10.json` go **10 → 3**. Only **T2** (job 869869,
running), **T3** and **T10** remain, all GPU or downstream of it.

**The finding, and it refutes the premise I handed the agent.** I asked it to confirm or refute
whether `concept_word` is non-empty on cells B/E, given it is **0 tokens in 6900/6900** on cell C.
It is **non-empty** — and the reason is that emptiness on C was never a property of the *bank*, it is
a property of the *cell*. One role census holds in **6,780/6,780** on both B and E:
`answer_format_instruction` 8, `user_instruction_scaffold` 11, `punctuation` 3, **`concept_word` 1**,
`chat_scaffold` 1, `response_header` 4 = 28 query-side tokens, with **`codeword` 0** and
`neutral_content` 0. **The exact mirror of cell C.**

Seeing it at all required making the role precedence **cell-aware**: `target_surface` *is* the
concept on B/E, so under the original codeword-first precedence the map would have reported
`concept_word: 0` on the very cells whose query names the concept — a matcher that could not see the
thing it existed to find, which is a class this project has now recorded several times.

**Dose parity holds**, which matters for PHASE 10 being answerable at all: ` bomb`/` knife`/` gun`
are **one subtoken each at `rel_end −10` in 6,780/6,780**, exactly as ` button` is — so the
dose-matched fallback is not triggered, and the `following` read site survives (`−9`, `' actually'`,
all four criteria 6,780/6,780). **H4 is not CANNOT ANSWER on read-site grounds.**

**T1** added `--cell {C,B,E}`; cell C's default path is regression-checked **240/240 byte-identical**
to the committed artifact. **T4** 13,560/13,560 agreement at the real call site, against a
re-derivation written for the check rather than imported, with the empty-needle guard firing 100/100
on planted input. **T6** query span protected in 13,560/13,560, three draws distinct as key sets with
**0 collisions**, smallest protected pool 117 — with the residual named rather than glossed: the
"3 distinct *output* hashes" half needs generation and is **not** claimed, staying a run-time VOID
gate. **T7/T8** re-run: 55/0 and 52/52 RED. **T9** an independent verifier whose
`assert_independent_of_analyzer()` enforces the independence against its own source as its first
self-test line — a verifier sharing the analyzer's assumptions verifies nothing.

**Three new defects, recorded rather than repaired away.** **PR058-D4**: 6 of 33,900 multi-subtoken
concept occurrences on cell B (4× `BOMB`, 2× `-knife`), all in the demo block, none in the query
span; cell E has 0. **PR058-D5**: checks A/A2 were comparing the target-surface count against
`n_codeword_occurrences` — a word that does not occur in a B/E prompt at all, so 5 vs 0 on every row;
repaired, mutation retargeted, now 6,780/6,780 PASS. **PR058-D6**: the committed cell-C token map
excludes **1 domain (115)** while PR-048 now names **3 (113)** — printed as a `[WARN]` with a
recorded `exclusion_readback` rather than silently repaired, since repairing it would rewrite a
pinned artifact.

---

## DCS-R-134 — PHASE 11's CPU blockers close; and PHASE 11 has no launcher
*2026-09-08*

Loader refusals on `configs/dcs_ts_pr059_phase11.json` go **9 → 4** (U2, U3, U8,
`analyzer_exists`). **The PHASE 9 instrument is provably undisturbed** — the harnesses were measured
before *and* after every edit and were identical both times: `dcs_ts_pr057_causal.py` **111/0** and
**90/90 RED**, `pr057_run_causal.py` **70/0** and **41/41 RED**. That mattered: this work edits
`score_behavior.py` and `dcs_extract_under_ko.py`, the instrument that had just produced a
confirmatory verdict.

**U1** — the declared-offset row selector is **one definition called at three sites**, and
`dcs_extract_under_ko.py` takes it **by import rather than restatement**, so that file's recorded
"second definition of K" hazard is not reintroduced and its last-K refusal stays intact. Producer and
analyzer return **identical positions for all five constructible scopes at seq_len ∈ {60,137,400,1024}
— 0 mismatches**. A non-negative offset refuses twice, at argument time and again at resolution.
Purely additive: the legacy branch is untouched and still taken when the flag is absent.

**U4** re-verified (`ok=true`, 6900/6900, K=5 matches S_A in 6900/6900, `neutral_content` 0) and then
**independently re-derived a second time** by the new verifier. **U5** 92/0, **U6** 80/80 RED.
**U7** — `scripts/dcs_ts_pr059_verifier.py`, **22/22 self-test and 22/22 mutations RED**, with
independence **enforced by test rather than claimed** (source scan plus a `sys.modules` assertion).
Its fixture uses a **per-row-varying `seq_len`** precisely so a pinned-absolute-index producer cannot
pass by accident.

**U2 is PARTIAL and stays open, and `PR059-D1` got worse.** The draw is implemented, reproducible
from a sha256-derived seed (never a salted `hash()`), and byte-equal across producer, `--plan` and the
independent verifier. But the arithmetic impossibility now names **three** scopes, not two: pools of
**6 / 5 / 0** against doses **22 / 23 / 28** for S_D, S_E and **S_G** — S_G's pool is **empty**. The
producer now **refuses by name** rather than drawing fewer rows and calling it dose-matched, which
makes the block explicit rather than removing it. **PR059-D1 still blocks the primary S_D-vs-S_E
contrast**; resolving it is a config-owner decision and a new preregistration, not a code change.

**`PR059-D2` — PHASE 11 has no launcher.** Every arm command `--plan` prints is addressed to
`scripts/dcs_ts_readout_multi.py`, which forwards **no** `--only-cell`, **no** `--knockout-scope` and
**no** row-set flag. U8's smoke run cannot be launched as written. This is the same class as PHASE 9's
Q4b — the analyzer and the arms exist, and nothing can actually run them.

---

## DCS-R-135 — PHASE 13 is CANNOT ANSWER, and the reason is stronger than "underpowered"
*2026-09-08* — `reports/DCS_TS_PR062_PHASE13_ASSESSMENT.md`; **no config written, deliberately**

PHASE 13 correlates representation destruction against downstream use. It was blocked on PHASE 9.
PHASE 9 has returned, and **the premise does not survive it**: no arm on this bank supplies both
halves of the mediation.

- **S2** moved the readout hard — O2 −0.642195, p at floor, 21/23 domains — but its **mediator is a
  CONSTANT**. Recomputed from the frozen `PR057_LIVENESS.jsonl`: domain-mean dose **9.6322**,
  between-domain SD **0.1843**, **CV 0.019**, **ICC = −0.0114** (basket 9.6034 / 0.1778 / −0.0115).
  A correlation against a constant is **undefined, not underpowered** — which is a much stronger
  statement than "we lack power", and it cannot be fixed with more domains.
- **S1** is the exact mirror: the mediator genuinely varies (ICC **0.2753**, CV 0.307) but there is
  no `y`. O2 = −0.002997 at p = 0.807519, and that movement sits **inside** the C1 band
  [−0.008842, +0.007934].
- Separately, S2's conjunct 3 failed, so the readout is demonstrably movable by **generic
  perturbation** at that dose. A mediation there measures the perturbation, not the representation.

**The precondition is in §32, not §31**, and it was found rather than assumed: §31 lists PHASE 13
bare, but CLAIM E — its claim, one to one — reads *"Only if: SAME bank; adequate power; valid
controls; domain-level estimator. **Otherwise: CANNOT ANSWER**."* Bank and estimator are met;
**valid controls** and **adequate power** both fail on measurements already in hand. A second gate
closes the other reading: CLAIM E says *behavioural*, and that instrument belongs to PHASE 12, which
is gated off pending a PHASE 9 positive that did not arrive.

**The deepest threat, stated rather than buried:** the mediator is fixed by design and never
experimentally varied, so whatever between-domain dose variation survives at S1 is activation
magnitude and domain difficulty — not representation content. Any coefficient would be confounded.
This is `R-097`'s lesson arriving in a second form.

**Power computed before any GPU was requested:** at n = 23 TEST domains a domain-level correlation
needs **r ≥ 0.556** (α = 0.05) rising to **r ≥ 0.652** at the Holm first step (α = 0.00833333) for
80% power; at n = 113 it would be 0.261–0.320.

**Reopening condition, recorded so this is a decision and not an abandonment:** a graded,
**within-domain-randomised dose ladder** that finds a working dose at which C1 is equivalent to zero.
If no such dose exists, PHASE 13 is **CANNOT ANSWER permanently on this bank**. The counterfactual
cost was estimated before being declined: ~60–80 arms / 14–18k rows / ~2.0–2.5 GPU-hours for a
minimal repaired version, and ~20–60 GPU-hours for one that actually answers CLAIM E, since that
needs generation plus a judge.

**No preregistration was written.** Writing one would have implied the phase is runnable.

---

## DCS-R-136 / C-128 — PHASE 10's T2 gate failure is OUR instrument; and Q0's pass was a POOLED pass
*2026-09-08* — `reports/DCS_TS_P10_CELLBE_OPTION_MASS.md`

GPU job 869869 scored all 2,784 rows of `button_bomb` on cells B/E and then failed its own
option-mass gate (median **0.01015** against 0.05). The runner stopped rather than burn the other
five banks — **~2.7 GPU-hours saved by failing closed**. The question was whether that number is a
property of the model or of us. **It is us.**

**The option set is wrong for cells B/E by bank construction.** `metadata.json` declares
`semantic_variants = {"concept": [" bomb"," Bomb"], "codeword": [" button"," Button"]}`, but the bank
records **`n_codeword_occurrences = 0` on every B/E row** — the word `button` never appears in those
stimuli at all. Measured `p_codeword` median **5e-6 (B) / 8e-6 (E)** against 0.030–0.059 on A/C. So
one option is dead and the other is the very word the question asks about. **One live option is not a
forced choice.** The read position is *not* the defect: the answer scaffold is byte-identical across
A/B/C/E and the readout sits at offset 0 after `"Answer:"` in every cell.

**What the model actually said, and it is a result rather than a diagnostic.** On **cell B** it is
confident and on-topic, naming the *referent*: ` Threat` 409 (35.3%), ` Explos` 266 (22.9%),
` Device` 125 (10.8%) — top-3 = 69.0%, with top-1 landing in the option set on **0.1%** of rows. On
**cell E the benign remap INSTALLED**: food-family top-1 rises **0.8% → 24.6%** while explosive-family
falls 24.4% → 16.6% (` Food` 39, ` Cake` 32, ` Sn`(ack) 27, ` Seeds` 24, ` Juice` 17, ` Fruit` 15).
**This answers PHASE 11's kill condition (3) with no GPU**: the cell-E remap does install, so that
CANNOT-ANSWER branch is not the one we are in.

## The finding that qualifies my own Q0 sign-off

`R-117` recorded Q0 as CLEARED on "`option_mass_gate = PASS` 6/6, the channel is engaged everywhere".
**That was a POOLED pass.** Broken out per cell and per dose: **A dose0 0.0416, A dose4 0.0593,
C dose0 0.0416, C dose4 0.3134** — *three of the four sub-cells sit at or below the 0.05 gate*, and
the 0.0825 headline is carried by **C dose 4 alone**.

**PHASE 9 is unaffected, and I checked rather than assumed it**: its population is cell C,
`semantic_one_word`, dose 4 — precisely the one sub-cell that passes strongly (0.3134). So the
verdict stands on the sub-cell that genuinely engages. But the general claim *"the concept-free
channel is engaged"* is narrower than I wrote it, and the honest form is **"engaged on cell C at
dose 4; at or below the gate on A dose 0/4 and C dose 0"**.

Also measured: **dose 0 decodes ` None` on 232/232 rows in all four cells** — correct, since the
queried word is absent from the passage, but it means **dose 0 is not a usable null for this channel
in any cell**.

## What PHASE 10 needs before any re-run

`--allow-tail-readout` is **declined**: the tail it warns about is real, and the repair is a correct
option set, not a waiver. Accepting a gate deliberately is only honest once the thing it warns about
has been checked and found fine; here it has been checked and found broken. Three items:

1. build the option set **per cell**, not once per bank from `rows[0]` — a `score_behavior.py` change;
2. decide B/E's real second option. The design's own `mapping_use_forced_choice` `{literal, mapped}`
   pair is the right instrument, but **`mapping_use_options` is `None` on all 22,272 rows**, so the
   bank must be **regenerated**;
3. compute the gate **per cell and per dose**, excluding dose 0 or scoring `"None"` in it.

The remaining five banks stay unrun until those are done. The written rows are not salvageable for the
primary readout — `summary.json`'s `reportable: false` is correct and stands — but the `top1_id`
column is salvageable as the diagnostic above.

---

## DCS-R-137 — the CORRECTED PHASE 9 verdict. Both classes held; C4 is the decisive number
*2026-09-08* — the answer to CLAIM C

The 4-hourly review found three defects in the verdict path. All three are fixed and the analysis
re-run. **Both verdict classes are unchanged** — which was the thing to check before anything else,
and the agent was instructed to stop loudly if either moved.

**Defect 1, and I reported it to the collaborator-facing summary wrongly first.** I said the probe
margin "moved significantly in the UNINTENDED direction". **It did not.** Verified on real rows: the
C5 bridge mean margin is **−0.94230** (the probe saturated on bomb) against the arm's **−0.55039** —
**P(bomb) FELL**, exactly as projecting the axis out should make it. The run's own JSON already
recorded `o1["moved_intended_sign"] = True`. The `[FAIL]` was a labelling bug at `:4386`: O2's
`expected_sign` (−1) was passed into `evaluate_success` and applied to **both** conjuncts, so O1 —
whose preregistered sign is **+1** — was scored against O2's direction. Each conjunct now takes its
own outcome's sign. The S1 block was also internally contradictory: the literal
`DECODABLE BUT NOT CAUSALLY USED` is reachable only via `o1_moved=True` yet printed three lines under
`[FAIL] 1_probe_moves_intended`. They now agree.

**The corrected per-condition table** (re-run, rc=0, 30 arms, 0 check failures; every outcome number
reproduced to the printed digit):

| conjunct | S1 was → now | S2 was → now |
|---|---|---|
| 1 probe moves intended | FAIL → **PASS** | FAIL → **PASS** |
| 2 semantic readout moves | FAIL → FAIL | PASS → PASS |
| 3 random control does not move | PASS → PASS | FAIL → FAIL |
| 4 holds across domains | FAIL → FAIL | PASS → PASS |
| **count** | 1/4 → **2/4** | 2/4 → **3/4** |
| **class** | **NEGATIVE** | **NOT A CAUSAL RESULT** |

**Defect 2 — C3 and C4 had run, passed liveness, and were analysed NOWHERE.** They are now on the
page, and C4 is the strongest evidence in the phase:

| arm | delta | p | equivalence 95% CI | ratio to arm | sign |
|---|---|---|---|---|---|
| `c4_samenorm_orth_s2` | **+1.237557** | floor | [+0.789922, +1.685192] | **1.93×** | **OPPOSITE** (5/23) |
| `c4_samenorm_orth_s1` | **+0.149133** | floor | [+0.118710, +0.179557] | **49.75×** | OPPOSITE (0/23) |
| `c3_vremap_s2` | −2.844680 | floor | [−3.153896, −2.535464] | 4.43× | SAME (23/23) |
| `c3_vremap_s1` | −0.047336 | 0.0781922 | [−0.100677, +0.006005] | 15.79× | SAME (17/23) |

A concept-free, norm-matched, equal-magnitude **orthogonal** ADD moves the readout **1.93× as far as
the concept edit at S2, in the opposite direction**. The site is perturbation-sensitive at this norm,
and the arm's movement cannot be read as the concept direction being used. That sentence is now
printed in the report rather than left for a reader to infer.

**Defect 3 — the dose the null was scoped to was DEFINITIONAL.** `frac_cellmean_spread_removed =
0.1656` is exactly cos²(v_bomb_specific, v_bomb): `cell_means` holds only cells A and C, so the
centred matrix is rank 1 and the figure is computable **without loading the model**. Nulls are now
scoped to the **measured** `cell_residual_frac_removed` (S1 L9 = **0.0936**; S2 L7–L14 =
0.1003 / 0.0396 / 0.0936 / 0.1412 / 0.1681 / 0.2058 / 0.2106 / 0.1729). The definitional figures print
only as bracketed "for reference only". A null with **no** dose still refuses, and a null carrying
**only** the definitional dose now refuses too.

**Observed:** `--self-test` 111 → **117 / 0**; `--mutate` 90 → **102/102 RED**, with 12 new mutations
including "a conjunct scored against another outcome's sign", "a null carrying only the definitional
dose", and "a built C3/C4 arm reported nowhere".

**Left open and named rather than buried:** Holm sets no alpha — the enforcement is an agreement
check, not the frozen file's literal reading; the measured dose is itself borrowed from the
development bank's cell means and the labelling does not say so per arm; C2/C7/H1/H2b remain absent
by construction; `_find_run` still takes newest-complete before the split guard (clean on this run,
and the guard is a hard refusal); and **C3 is the raw axis, not remapping-only — no arm in this
design isolates remapping**, which the printed C3 sentence now says.

---

## DCS-R-138 / PR-061 — PHASE 11's launcher exists; its primary contrast is CANNOT ANSWER, for a stated reason
*2026-09-08*

`src/boombness/pr059_run_localisation.py` closes `PR059-D2`, the Q4b-class hole where the analyzer,
arms and verifier all existed and nothing could run them. Observed: **`--self-test` 51/0**,
**`--mutate` 43/43 RED**, **`--plan` 78 arms** matching the analyzer exactly (76 constructible),
**`--stage smoke --split train --dry-run` rc = 0** with no model loaded and nothing written. The argv
was validated end-to-end against the *real* `score_behavior` on CPU — every flag parsed, the scope
resolved to `S_C: 1 row [-10]`, population bound to 1160 — and then refused on a deliberately wrong
`--expect-n`, before the model loaded.

PHASE 9's two hard-won lessons were built in rather than relearned: **C-123**
(`assert_expect_n_agrees_with_limit`, mutations M01–M03 covering both directions) and **C-124**
(`assert_stage_has_no_prior_verdict` before any arm runs, M04–M06).

**PR059-D1 is decided — option 3, and the headline is honest.** PHASE 11's declared primary contrast
**S_D vs S_E cannot be run as designed: CANNOT ANSWER, for a stated reason.** The dose-matched control
exists only where `28 − m ≥ m`, and S_D/S_E/S_G have pools **6/5/0** against doses **22/23/28**. Those
three are **demoted, not deleted**: still run, still reported, still entering Holm at their own p,
still carrying the nondemo-key control — but success condition 3 is **unevaluable** for them, and
success is conjunctive.

The rejected options are recorded with why: demo-block draws **change the causal graph** and the
selector forbids them; overlap produces **a control that cannot fail**; and promoting S_C vs S_F would
make the headline the comparison the design itself calls *"close to uninformative"* — choosing the
contrast that survives rather than the one that answers the question.

**A fifth option was found and deliberately NOT taken**, which is the part worth keeping: control the
**difference row** — `S_D ∪ {one random non-codeword row}`, m = 1, pool 5, exactly 23 rows against
S_E. It is constructible. But it is a **new arm** and would require editing the **frozen** analyzer,
so it is named for a successor preregistration instead of taken unilaterally.

**What the decision costs, stated plainly:** the codeword-row question goes unanswered; rows-vs-cells
is unseparated for the three largest scopes; and any S_D−S_E difference is an **upper bound, never an
estimate**.

**Four new defects, reported rather than fixed** — each needs a file held by concurrent work, and the
agent stopped rather than reach into it:
- **`PR059-D4`** — the analyzer's `liveness_gate` reads the **PR-057 project-out schema**, but the
  knockout producer writes none of `hook_fired_count` / `n_cells_edited_expected` /
  `n_cells_edited_realised`. The runner **refuses to invent them**, which is right: inventing them is
  how a dead hook reads as a clean null.
- **`PR059-D5`** — analyzer manifest **78** against verifier expected **82** (S_G's nondemo controls
  +6, bridge arms −2). A complete run would fail R5 **both ways at once**.
- **`PR059-D6`** — **null L-N1 is not constructible**: `DisabledHookBridge` cannot bridge
  `ScopedAttentionKnockout`, which exposes `_handles` rather than `_hooks`. Measured on CPU, not
  inferred.
- **`PR059-D7`** — `analyse()` has **no verdict path**, so `analyzer_exists` stays false. This is
  PHASE 9's `A4` arriving again in a second phase.

`configs/dcs_ts_pr061_phase11_amendment.json` records the decision: clean under the loader (FROZEN,
18 hashes verified, 12/12 mandate-§21 fields) and still refusing `--for-extraction` with **7
refusals** (V3, V8, V10, V11, V12, V13, `analyzer_exists`). Repo tests **676 passed**, run to
completion.

---

## DCS-R-139 / PR-063 — PHASE 10 repaired with NO regeneration and NO pin moved
*2026-09-08*

The diagnostic recommended regenerating the bank. **Regeneration was not needed, and it would have
been expensive in a way the recommendation had not costed**: `bank_file_sha16` is pinned across
`PR-048`, `PR-057`, `PR-060`, `PR-058` and `PR-059`, so regenerating `ts116m` would have invalidated
the provenance of a **completed confirmatory result** — PHASE 9, 30 arms, 6,900 rows.

**The correct option set was recoverable from what the bank already holds.** The field is
`pools["<demo_pool_domain>|benign"]["natural_word"]` in `demo_pools_116dom.json`, whose
`_meta.content_sha16` **`976aa2b0b617118d` is already `population.pools.shared_pools_sha16` in the
frozen PR-058** — the evidence was pinned by the preregistration all along. Cell E's demonstrations
are the benign pool with `carrot` substituted by the concept: *"a large crate of **bomb** puree"* ←
*"…of **carrot** puree"*. So the honest forced choice on B/E is **{concept, carrot}**.

**Coverage 66,816 / 66,816** cell-B and cell-E rows across all six banks, 0 unresolved, 0 degenerate;
`natural_word` is `carrot` in 116/116 benign pools; `demo_pool_domain == domain` on 133,632/133,632
rows. Corroborated independently: **inverting** the substitution on cell-E demo blocks reproduces a
verbatim benign-pool sentence on **149,922/150,336 = 99.72%** of demo lines.

The rule keys on **`query_surface`, not on cell name or demo valence** — because cell B's *harm*
pool's `natural_word` **is** the concept, and H1–H3 needs B and E on one axis: `codeword` →
`{concept, codeword}` (A/C, unchanged); `concept` → `{concept, benign natural_word}` (B/E).

**A/C are provably untouched.** The "before" was taken from the `metadata.json` the two runs on disk
**actually shipped**, not re-derived from the code under test — and all **6/6 banks reproduce their
pre-amendment option set with an identical sha16**. `signals.py` is unmodified. `score_behavior`
now *refuses* if a bank-pair cell fails to reproduce the run-wide set, or if one cell resolves to two
sets, and `--print-cmd-only` reproduces job 869869's command line **byte for byte**.

**The per-cell/per-dose gate, computed on rows already on disk** (no GPU): B/n4 **0.012608** and
E/n4 **0.015763**, both BELOW gate — and, confirming `C-128`, **A/n0 and C/n0 (0.041589) "would have
been BELOW"** had they been gated. Only A/n4 (0.059274) and C/n4 (0.313414) pass. **Dose 0 is
excluded from the gate with evidence**: argmax is `" None"` on **232/232 rows in every cell of both
runs**, so neither option is the answer — the instrument is **inapplicable**, not the model
disengaged. Excluded rather than scored `None` because a `None` median propagates as a NaN refusal.

**Not settled, and stated as such:** `p(carrot)` was never scored and cannot be computed from the
written rows (`" Carrot"` is argmax on 0/1160 cell-E dose-4 rows, which bounds nothing). **Whether
the repaired instrument clears 0.05 is item A2, still open** — which is exactly what the pre-run is
for.

**Observed:** `pr058_symmetry --self-test` 55 → **57/0**, `--mutate` 52 → **56/56**; the verifier
16 → **18/18**, with new **X17** replaying job 869869's own defect (cells B/E scored against the bank
codeword) and X18 (option set unrecorded), both RED on a new check R9. Amendment clean (16 hashes,
12/12 fields), `--for-extraction` **4 refusals** (A2–A5). **The parent PR-058 still verifies clean at
17 hashes — no pin moved.** `pytest tests` to completion: 1693 passed / 4 failed, the four
pre-existing in `test_prompt_families_strict.py`.

**Two source-text pins forced design decisions and neither was weakened.**
`tests/test_option_mass_gate.py` pins the pooled loop's exact code, so the refactor was **reverted**
and the two copies are held together by a runtime equality check instead (equal on 3000/3000 random
inputs including NaN/None). `tests/test_readout_liveness.py` AST-pins the literal
`_semantic(templated)` to prove the readout runs **inside** the intervention ExitStack; the first
attempt broke it, so the per-row answer set now travels through a one-slot cell and **the call site
is unchanged**.

**Defect `A9`, recorded not fixed:** the pooled tail gate's *failure* test reads `med` (upper-middle)
while its `reportable` field, its comment and its test all read `median_true` — biased toward
passing. Swept across 244 runs / 241 buckets: **230 differ, 0 verdicts differ.** Left as-is; the new
per-cell gate reads `median_true`.

---

## DCS-R-140 / C-129 — PHASE 10's primary is CANNOT ANSWER; and cells B/E are codeword-DEGENERATE
*2026-09-08* — jobs 870154 (button_bomb) and 870186 (basket_bomb)

**Item A2 is answered: the repaired instrument does NOT clear the gate.** With the correct
`{concept, carrot}` option set — the one recovered from the already-pinned benign pool —
**B/dose4 = 0.012711** and **E/dose4 = 0.018079**, both roughly **3× below the 0.05 gate**. Swapping
the dead `button` option for the real remap target moved it by about half a percentage point.

The reason is in what the model says: it answers with a **category**, not with either declared
option — ` Threat` 35.4%, ` Explos` 22.8%, ` Device` 10.7% on cell B. **A two-option forced choice
cannot capture a categorical answer whichever two words are chosen.** So PHASE 10's primary
concept-free readout is **CANNOT ANSWER on measured grounds**, and the preregistered consequence
holds: a disengaged primary channel is not a licence to fall back on the display channel.

**A provenance defect (`C-129`) that nearly misled me.** The run's `metadata.json` still advertises
the **old** `{" bomb"," Bomb"}/{" button"," Button"}` set, which reads as though the repair never
applied. It did: `summary.json` records `semantic_options_mode = "per_cell_remap"`,
`semantic_options_source = "benign_pool_natural_word"` and
`semantic_option_words_by_cell = {B: {concept: bomb, codeword: carrot}, E: {...}}`. **The run
artifact does not record the option set it actually used** — anyone reading `metadata.json` alone
would draw the wrong conclusion about a published number. Recorded, not fixed here.

## The structural finding, which matters more than the gate number

I re-ran on `basket_bomb` before generalising, because `R-116` had established that button and basket
differ enormously (installation 92/113 vs 46/113) and "the channel is unusable on B/E" is a claim
about a population. **Every bucket came back byte-identical to button_bomb** — median 0.010557, p90
0.058872, B/dose4 0.012711, E/dose4 0.018079, to six decimals.

Verified rather than assumed: **232/232 prompts are byte-identical across the two banks on cells B
and E** (116/116 on each cell, by `prompt_sha16`).

**Cells B and E are codeword-DEGENERATE by construction.** They never contain the codeword — that is
the same `n_codeword_occurrences = 0` fact that broke the option set — so the `button_*` and
`basket_*` banks hold *literally the same* B/E prompts. Consequences:

- **`PR-058` declares a six-bank population, but for its PRIMARY cells there are only THREE distinct
  populations**, one per concept. The codeword dimension is degenerate on B/E.
- **PHASE 10's cell-B/E arms cannot address lexical transfer at all.** Any "button → basket" question
  is unanswerable there, and must not be asked of these cells.
- The A2 result above is therefore already established on the **complete** B/E population; a third
  bank would add nothing either.

**And the mistake is mine to own: ~17 minutes of GPU spent re-scoring identical prompts.** The a
priori reason to check a second bank was sound — R-116 is exactly the precedent — but the check
itself was answerable on **CPU in seconds** by comparing `prompt_sha16` across banks *before*
submitting. **New rule: before spending GPU to compare two populations, verify on CPU that they
differ.** Byte-identical inputs cannot produce different results, and finding that out from a
scheduler is the expensive way.
