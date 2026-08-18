# Handoff prompt — Boombness Objective Sprint, continuation

Paste everything below the line into a fresh Claude Code session started in
`/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood`.

---

implemnt this plan . document your progress in external md where we would be able to track your
progress. follow the insturctions in the plan, dont write a lot of code if you dont need and reuse
the exsiting code from the artical as much as you can! dont skip on any stage from the plan unless
you have to - you can consult with me. use subagetns to run things in paralel - whatever you can
paralel without herting the results- do it. our goal is to add to this paper and find new tings with
this reseach. allways double check yourslef that you dont have a bug and do a code review for
yourslef. commit and push after you do some progress so will be able to track it. ultrathink
ultracode fan out subagnets /loop every 30m

---

## Context you are inheriting

This is a Tel Aviv University MSc project (Omer Yosef, advisor Mahmood Sharif, collaboration with
Matan Ben-Tov) on the mechanistic interpretability of doublespeak jailbreaks. A previous session ran
most of this sprint. An adversarial audit (47 agents, find→refute) then found 31 confirmed defects.
**You are not starting from zero and you are not starting from a clean base.** Read this whole
section before touching anything.

### The three documents that govern the work

| file | what it is | how to treat it |
|---|---|---|
| `docs/BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md` | **THE PLAN.** 20 sections, written 2026-08-16. | Authoritative. Do not deviate without asking me. |
| `docs/BOOMBNESS_SPRINT_EXTERNAL_CRITIQUE_2026-08-18.md` | **THE AUDIT.** 31 confirmed defects, tiered, with file:line and a recommended fix order. | Authoritative on what is broken. Start here. |
| `docs/BOOMBNESS_SPRINT_PROGRESS.md` | Execution log, ~394KB, 7 retractions, tick-by-tick. | Rich but long and partly stale. Grep it, don't read it linearly. Its clock is wrong. |

Deliverables that already exist and are **stale in specific ways the audit names**:
`reports/boombness_objective_sprint_report.md` and
`reports/boombness_objective_sprint_short_update.md`.

### What already exists (do not rebuild any of this)

**Code** — `src/boombness/` (31 modules, all working except where the audit says otherwise):

- `prompt_families.py` — the aligned prompt-bank generator (the 2×2 design). 
- `demo_pools.py`, `make_manual_review.py`, `tokenization_audit.py`
- `signals.py`, `extract_boombness.py` — activation extraction, direction fitting, logit lens
- `common.py` — `RunDir` / `FailureLedger` / provenance. **Every new script must use these.**
- `probes.py`, `role_probes.py` — 6 probe regimes, domain group-k-fold, shuffled controls
- `aggressive_patching.py` — plan §5 transplant + additive steering
- `surgical_knockout.py`, `dominance.py`, `diagnose_knockout.py` — plan §10
- `score_behavior.py`, `judge_boombness.py`, `coherence_gate.py`, `refusalness.py`
- `analyze_g1_g3.py`, `analyze_g2.py`, `analyze_g8.py`, `analyze_g9.py`, `analyze_g11.py`,
  `analyze_g64.py`, `analyze_position.py`, `analyze_role.py`, `analyze_steering.py`,
  `analyze_boombness.py`, `reanalyze_corrected.py`, `retraction_sweep.py`, `compare_runs.py`
- `slurm/run_boombness.sh` — **the single GPU launch wrapper.** Read its header comments before
  submitting anything; they encode hard-won SLURM lessons (nodelist must be reduced not `--exclude`;
  `--export` truncates comma lists silently; argsfiles must be on the shared FS, never `/tmp`).

**Data** — `data/boombness_prompts/`:
- `boombness_prompt_bank.jsonl` — 2352 rows, 912 families, 6 domains, file sha256[:16] `71bea179345ed118`
- `boombness_prompt_bank_meta.json`, `demo_pools.json`, `manual_review_50.md`, `role_style_block.jsonl`

**Outputs** — `outputs/boombness/` (gitignored; key JSONs are force-added). ~130 completed runs with
`config.json` / `metadata.json` / `results.jsonl` / `summary.json` / `DONE.json`.

**Reference code you must reuse rather than reinvent** — `external_repos/interp-jailbreak/`
(Matan/Mor's attention-hijacking repo, `.git` removed as the plan requires) and the notes already
written from it: `notes/interp_jailbreak_best_practices.md`, `notes/three_codebase_adoption.md`,
`notes/boombness_reuse_inventory.md`. Also in-repo: `doublespeak_causality/pair_common.py` and
`ds_common` carry house helpers (`patch_layer_sweep`, `norm_matched_random`,
`find_word_occurrences_in_text`, `apply_template`) that the sprint sometimes reimplemented instead of
calling — prefer the house helper.

### What the sprint found so far (so you know what you are defending or overturning)

- **G1 (plan §5):** the codeword's meaning is retrieved from the demonstrations at answer time, not
  stored in the token. Best current estimate **+68% of span, CI [+50%, +95%], 24 families, 6 domains**
  (`outputs/boombness/g1_stratified.json`). The report still headlines a superseded +84% on n=8/2 domains.
- **G2 (plan §9):** Boombness modestly predicts ASR on Llama-3.1-8B (ρ≈+0.307 at L12, n=234), and
  **does not replicate on Qwen3-14B**.
- **G3 (plan §10):** the retrieval is attention-carried and massively redundant — **but see audit
  Tier-1 #3, the edge ranking is measured at the wrong token, so G3 is not actually established.**
- **G4 (plan §12):** steering the axis suppresses ASR at both signs → the pure objective is dead.
- **Two late causal results** (added 2026-08-18): (a) adding Boombness + removing refusal more than
  doubles ASR, but the gain appears where the mapping is never taught, so its mechanism was retracted;
  (b) projecting out `d_surface` raises attack success on Llama (+0.056 vs control), does not
  replicate on Qwen3. **Both are compromised by audit Tier-1 #1** — their comprehension control does
  not measure comprehension.

### Models / environment

Primary `meta-llama/Llama-3.1-8B-Instruct` (bfloat16, default SDPA — do NOT disable flash).
Replication `Qwen/Qwen3-14B`. GPU work goes through `slurm/run_boombness.sh` on L40S nodes.
The **login shell has no scipy/sklearn** — analysis scripts need the conda env; resolve its exact
path early (the report's repro block still has a `PY=<conda-env>/bin/python` placeholder) and record
it in your progress doc. Shell is zsh: unquoted `$VAR` does not word-split and `$var:x` is a zsh
modifier, so build argsfiles with `printf` and grep them back before submitting.

---

## Your task, in order

### Phase 0 — read and orient (no compute)
Read the plan and the audit in full. Read `reports/boombness_objective_sprint_report.md` §0 and the
two ★ sections at the end so you understand the contradiction you are being asked to resolve. Create
your progress document **now**, before any code:

```
docs/BOOMBNESS_CONTINUATION_LOG.md
```

It must carry, and stay current: a phase board (one row per plan section, status DONE / PARTIAL /
NOT DONE / DEFERRED-WITH-REASON), a gate table, a defect table tracking the audit's 31 findings from
open → fixed → verified, a running retraction/correction log, and a tick log. Update it every time
you finish a unit of work, not at the end.

### Phase 1 — fix what is broken before producing anything new
The audit's recommended order, which I endorse. Each of these currently invalidates a published claim:

1. **`analyze_g8.t_sf`** (`src/boombness/analyze_g8.py:52`) — the beta continued fraction omits the
   symmetry transform, so it is wrong for all |t| < 1.69 at df=5, always anticonservatively. It is the
   sprint's t reference (`analyze_g9` imports `t_sf_2sided`, `reanalyze_corrected` imports `t_crit`).
   Replace with `scipy.stats.t`. Then **recompute every clustered p in the sprint** and diff against
   what is published. Proof it is wrong, needs no rerun: `g9_three_predictor_lastpos.json` publishes
   `p_cr1=0.766` beside `p_cr1_normal=0.991` for the same term, which is impossible.
2. **The §2.6 comprehension readout** (`score_behavior.py:308`) — it scores the leading-space tokens
   `' literal'`/`' coded'` at a position where the model emits the bare forms. Measured on the
   committed baseline: the two options hold a median 4.4e-05 of next-token mass, and 0 of 288 rows
   exceed 1%. Fix it (sum `full_word_ids`, minding that the option sets are asymmetric — 4 variants
   for "literal", 2 for "coded" — or move the readout behind a forced prefix), then **re-run all of
   report §4b**. Until this lands, no intervention in this project can be called non-destructive.
   Also: `semantic_forced_choice` (288 rows, built to fix exactly this) was generated and never scored
   by any run — score it.
3. **`analyze_steering.py:151`** — unconditional `KeyError: 'wilson95'` (line 139 renamed the key,
   line 151 was not updated). The clustered-CI commit has never executed; the committed
   `steering_analysis.json` is the pre-fix file the report cites as current. Fix, re-run, replace.
   While there: `:66` enforces `require_done` on the baseline only, never on the intervention arms.
4. **`surgical_knockout.py:271`** — `dst = dsts[0]` is always the codeword position, the destination
   retraction #3 called fatal. The knockout was fixed; the **edge ranking** was not, so G3's
   topk/bottomk null cannot distinguish "these edges don't matter" from "ranked at the wrong token".
   Rank at `readout_pos`. Note `:288` also filters `i < dst`, silently truncating the demo set.
   Then re-run G3. Also fix `:239` (uses one split's directions for all rows → ~54% scored in-sample,
   giving the targeted arm an advantage the controls don't get) and `:225` (head-truncates a
   domain-prefixed sorted list, and `--n-families` counts prompts not families — the "6 families" runs
   are 3 domains × 2 splits).
5. The remaining Tier-2 items in the audit: the permutation-p / ρ estimand mismatch in `analyze_g64`
   / `analyze_g2` / `analyze_g9`; G2's uncorrected 20-column layer selection; `reanalyze_corrected`'s
   Holm family being 10 layers not 32 (at m=32, L4 stops being rejected and the report cites L4 twice
   as its multiplicity backstop); the `--fit-dir` consumers that never validate `payload["meta"]`;
   single-draw "control bands" in `aggressive_patching:461` and `probes:236`; the tautological
   readouts in `aggressive_patching:188` (readout layers overlap patched windows — call the house
   `ds_common.patch_layer_sweep`, which forbids exactly this).

**Do not start Phase 2 until Phase 1 is done and the affected numbers are recomputed.** Report
honestly if a fix changes a conclusion — that is the expected outcome for at least G3 and §4b.

### Phase 2 — close the plan sections that were never done
- **Plan §15 report sections that do not exist:** item 2 (what was implemented), 6 (aggressive
  patching results), **7 (Boombness metric comparison)**, 14 (negative results), 15 (failure modes),
  16 (recommended next experiments). Item 7 is the substantive one: §6.4 was run
  (`outputs/boombness/g64_metric_comparison/`) and grepping both reports for "metric comparison",
  "probe_boombness", "direction_boombness", "logit_lens" returns zero hits. Its answer is unflattering
  (`common_all_three` = 72 of 270), which is why it belongs in the deliverable.
- **Plan §10.4 arm D (remove both)** ran, was judged, is in `causal_claims.md`, and appears in neither
  report — despite showing a harm-type-dependent sign flip (+0.681 on `direct_harmful` when removing
  both, +0.000 when adding). Put it in.
- **Named outputs never produced:** `correlation_summary.json`, `regression_summary.md` (plan §9), and
  9 of the 12 named plots — all five §8 plots and all four §9 plots.
- **Plan §5.2's alpha sweep** ran 4 of 6 doses, and **0.25 — the dose carrying every behavioural
  claim — is not one of them.** Run it.
- **Plan §9 decision question 5** ("does it hold controlling for number of examples?") is unanswered:
  `n_examples` is used only as a filter in `analyze_g9.py`, never as a regressor. Since it plausibly
  drives both Boombness and ASR, ρ=+0.307 is currently unguarded against a dose-response confound.
- **`analyze_g9`'s role-identifiability gate** (`:207`) tests family overlap on a `family_id` string
  that embeds the style name, so overlap is 0 by construction and the gate would refuse even after the
  design is fixed. The instinct (refuse to fit an unidentifiable term) is right — make the test real.

### Phase 3 — the experiment most likely to produce something new
**Run at least one arm on ClearHarm.** It is already integrated in this repo (`data/clearharm/`,
`scripts/build_clearharm_manifests.py`, five manifests under `data/manifests/`) and plan §14 asks for
it; the sprint never used it and never said so. Every ASR number to date comes from the sprint's own
generator. The report already concedes the arm-F gain is largest where the mapping is *never taught*
(`benign_remap` +0.267) — the signature of a prompt-bank artifact. An external harmful set is the
cheapest experiment that discriminates "real mechanism" from "bank artifact", and it is the single
highest-value new result available.

Then decide, with me, what to do about **plan §4.1's designed variance**: `strength`, `consistency`
and `example_position` were generated into the bank exactly as the plan specifies and are analysed by
nothing. They are also confounded as built — `near` gets 0 filler sentences while `far`/`distributed`
get 6 (403 vs 792 chars); `conflicting` leaves the demos consistent and appends a counter-mapping
sentence containing an extra codeword occurrence in the closest-to-query position; `strong`/
`aggressive` inject the literal concept token into a codeword-surface prompt. Either fix the generator
and analyse them, or delete them from the bank and say so. Generated-confounded-unexamined is the
worst of the three states.

### Phase 4 — rewrite the deliverable
The report currently states its conclusion both ways. The gate table plus L306/L534/L662/L698 say
"outcome B, not causal, §12 was not built, do not build the objective"; L841 says "§18 = B is
WITHDRAWN, §12.2 is REOPENED". Neither is marked. `§0.3`, cited twice as the causal evidence,
**is not a section that exists**. Fix by: one conclusion stated once at the top; withdrawn verdicts
in a retraction table, never in the gate table; the two ★ sections merged into the body; G1's headline
promoted to the `g1_stratified` numbers (+68%, 24 families, 6 domains); the `§0.3` pointer resolved.
Then re-run `retraction_sweep.py` across **all** deliverables.

Also fix, per the audit: the "matched footing" incremental-R² table gives refusalness 5 predictors and
Boombness 1 (§19 Q7 and the short update's "done correctly" both rest on it, and it flips at matched
df); the second causal result's "harmful yes, benign no" profile is one significant cell out of six
(p=0.0077 / 0.363 / 0.438) while the *Qwen3* column's equivalents are annotated "(n.s.)" eleven lines
later; and the Llama-vs-Qwen3 non-replication compares a 512-token run against a 192-token run, a
variable the log itself records as halving the Llama effect.

---

## Standing rules — these are project rules, not suggestions

**Research discipline (from the plan, §2):**
- Every run saves `config.json`, `metadata.json`, `results.jsonl`, `summary.json`, `plots/`. Use
  `common.RunDir` — it enforces this and refuses to `finish()` without a `FailureLedger`.
- **No silent failures.** Skipped examples, tokenization mismatches, missing target tokens, OOMs,
  malformed generations, judge failures — all counted with reasons in `summary.json`. The audit found
  four places that violate this; do not add a fifth. (`score_behavior.py:425` has no `else` in its
  query-kind dispatch, so an unhandled kind is counted as a success with no output — fix it.)
- **Smoke test first, always:** 2–4 prompts, verify token positions by hand, verify target token
  indices, verify activation shapes, verify the result files. Only then sweep.
- **Tokenization audits are mandatory** for any new codeword/concept. The current bank forces
  single-token by construction; a second concept pair will need real span handling.
- **Controls are mandatory** (plan §2.5, nine of them) and a control must be a *band*, not one draw.
- **Never confuse lowered ASR with causal understanding.** Comprehension control on every intervention
  — which is why Phase 1 item 2 blocks everything downstream.
- Record `seed` and `tokenizer_revision` — plan §2.1 requires both and **neither appears in any of the
  145 config.json or 130 metadata.json files today.**
- Two different functions are stored under the same key `bank_content_sha16` —
  `prompt_families.py:568` hashes concatenated per-prompt shas, `common.py:235` hashes file bytes.
  Nothing ever compares them, though the docstring says that is the point. Give them distinct names
  and write the comparison.

**Engineering:**
- Reuse before you write. Check `notes/boombness_reuse_inventory.md`, `external_repos/interp-jailbreak/`,
  and `doublespeak_causality/pair_common.py` before adding a function.
- **A guard that has never been tested against a case it should fail is not a guard.** This project has
  shipped four guards that never executed. Every guard you write ships with a test that fails it.
- **Address things by identity, not by an incidental property.** All four dead guards matched on a
  filename, a tag prefix, an mtime, or a line number.
- Layer indexing: HF `hidden_states[0]` is the embedding output, so layer L is `hidden_states[L+1]`.
  Watch the transformers-5.x tied final-norm entry — `extract_boombness.forward_hidden` handles it.
- Watch the absolute-position-index bug class: a position computed from `example[0]` and reused as an
  absolute index across other examples. It has hit this repo twice.

**SLURM (house rules, learned expensively):**
- No job dependencies. Max ~6 parallel. L40S only. Do not trim runs to fit.
- Argsfiles on the **shared filesystem**, never `/tmp` (node-local → job dies in 3s).
- `--export` silently truncates comma-containing values; verify row counts after "COMPLETED".
- Reduce `--nodelist` to skip a node; passing `--exclude` nullifies the wrapper's nodelist.
- Cap ~2 model-loading jobs per node (3 on one node = 16× weight-load slowdown).
- PENDING over 30 min → `scancel` and resubmit with a widened nodelist.
- Tell a hung job from a slow one via the weight-loading bar in `.err`, not `squeue`.

**Subagents:** parallelise freely for code reading, statistics, plan-coverage sweeps and independent
verification. **But** subagents that read raw jailbreak prompt text or raw model generations get
terminated by a safety classifier — keep text work in the main loop and delegate scalar/metadata/code
work. Give verifiers an adversarial brief ("your default is that this finding is wrong").

**Git:** commit after each unit of progress with a message that states the finding, not the activity.
`outputs/` is gitignored — force-add the analysis JSONs that back a claim, as the existing history
does. Backticks in `git commit -m` silently delete the enclosed word in this shell; avoid them.

**Reporting:** negative results are the deliverable too. Do not claim "we found the mechanism" unless
all six of plan §13's criteria hold. Redact harmful completions; store judge scores, not raw outputs.

---

## The bar

The previous session self-caught seven retractions, which is more than most published work manages.
Its failure was not dishonesty — it was that the **deliverable was never re-derived from the current
state of the evidence**. Every number in your final report must be regenerable by a committed script
from a committed artifact. If you cannot point at the script and the artifact, the number does not go
in.
