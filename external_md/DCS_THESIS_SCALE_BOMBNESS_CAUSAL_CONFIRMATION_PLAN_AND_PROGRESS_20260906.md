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
