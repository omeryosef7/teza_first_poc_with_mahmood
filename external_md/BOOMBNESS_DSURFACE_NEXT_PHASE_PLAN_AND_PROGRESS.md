# `d_surface` NEXT PHASE — plan, decision gates, and live progress log

**File:** `external_md/BOOMBNESS_DSURFACE_NEXT_PHASE_PLAN_AND_PROGRESS.md`
**Opened:** 2026-08-23 17:20 IDT
**Repo:** `first_poc/teza_first_poc_with_mahmood`, branch `behavioral-causality-sprint`
**HEAD at open:** `91e30a62` ("section 4b was running on the readout R-6 withdrew", 2026-08-23 17:09:38)
**Owner of this phase:** this Claude session. SLURM submissions for this phase are owned here and
logged in §5. Peer sessions notified 17:19 — see §0.4.

> **This file is the authoritative live research log for this phase.** It is append-oriented:
> superseded conclusions are marked `⛔ RETRACTED — reason` with the corrected statement beside
> them, never silently overwritten.

---

## 0. STARTING STATE (Phase 0 gate)

### 0.1 What is already known — read before citing any old number

The original chain
`Boombness → predicts ASR → causally increases jailbreak behaviour → becomes a GCG/MAC objective`
**did not survive.** The current state, condensed from
`reports/SPRINT_SUMMARY_2026-08-16_TO_08-23.md` (commit `8bd07054`, itself written by re-deriving
445 figures from committed artifacts):

* **G2 is RETRACTED (R-18).** `d_surface` does not predict attack success on clean rows.
  Published n=234 ρ_within = +0.26178047909981317 (p 0.0004997501249375312) → clean n=90
  **−0.05180076147796621** (p 0.657671164417791); powered n=108 **−0.06601851932290928**
  (p 0.49325337331334335).
* **G4 is a directional null.** Both signs of `d_surface` steering suppress ASR. **Do not build the
  original GCG objective.**
* **Removing `d_surface` raises ASR** on AdvBench-495 held-out: L8 **+0.04242424242424243** (21 net
  flips), L12 **+0.03636363636363636** (18), L10 +0.03232323232323232, L6 +0.01818181818181818.
  Continuous domain-clustered at L8: **+0.030519369707034255**, p_cl 0.008929531014546195,
  CI [+0.00885299048927438, +0.052185748924794134]. Band ≈ **L6–L14**, core L8–L12.
* **Refusal is the far larger Llama channel:** arm C **+0.2061** (102 flips), arm D **+0.2869**
  (142 net / 143 gross).
* **Qwen3-14B is qualitatively different:** `d_surface`@L11 gives **+0.38095238095238093**
  (p_cl 0.00030870570185738953) while refusalness@L20 does nothing (`C20` = 0.16666666666666666
  against a 0.17142857142857143 baseline).
* **G1 strong:** meaning comes from the demonstration block. `demos_only|L18` transplant
  **+0.6887043836439078** of span, CI [+0.5127769879731333, +0.9741707744164648]; `query_only`
  **−0.5700186200834122** (wrong direction); whole-prompt null.
* **G3 strong and redundant:** full demo-block attention knockout recovers **75.15%** of the
  text-deletion ceiling (−13.436758967737356 of −17.878933541476727) at **81,706.67** edges cut;
  sparse top-k does **not** work (+0.019611094146966934, sem 0.016518567912713653).
* **DOSE CONFOUND (R-25):** `d_surface` is essentially **PC1** of the cell-mean span
  (cos 0.9998–1.0000). It removes 0.81–0.88 of the cell-mean spread; every in-subspace control
  removes ≤ 0.13. `dose_gap_arm_over_max_control` = 10.96 / 7.36 / 6.17 / 6.83 at L6/L8/L10/L12,
  `dose_confounded: true` at all four.
* **No concept transfer (R-23/R-24).** E12 retracted in full. Call it `d_surface_carrot_bomb`, not
  "Boombness" and not a "bombness direction".
* **The methodological gap this phase exists to close:** G1/G3 are measured on
  `semantic_one_word` / readout prompts; behavioural ASR is measured on `behavioral` prompts.
  **Nobody has knocked out the retrieval pathway and measured jailbreak behaviour on the same rows.**
* **The final multiplicity verdict on direction specificity is negative.**
  `outputs/boombness_followup/angle24_specificity_FULL.json` →
  `multiplicity_over_depth_family.holm_m4` = L12 0.0732219168023166, L10 0.0732219168023166,
  L8 0.20706049565437049, L6 0.6782717805522958; `rejects_at_0.05` is **empty**. The
  0.0136/0.0276/0.0347/0.0347 tail widely quoted elsewhere is **single-draw and superseded**.

### 0.2 Phase 0 checks — RESULTS

| check | result |
|---|---|
| branch / HEAD | `behavioral-causality-sprint` @ `91e30a62`; remote is at the same commit |
| uncommitted result-changing modifications | **none** — `git status --porcelain -uno` empty, 0 untracked |
| guard suite (`check_all.py`) | **6/6 pass** (run 17:05 and 17:16 at HEAD) — retraction_sweep, canonical_figures, verify_report_numbers, markdown_structure_check, pvalue_hygiene_check, plan_coverage_check all exit 0 |
| SLURM queue | **EMPTY** for the account at 17:19. No jobs of ours or a peer's running |
| **OpenAI credits** | ⬆ **RESTORED.** `POST /v1/chat/completions` with `gpt-4o-mini` using the repo `.env` key returned **HTTP 200** at 17:18. **The 2026-08-23 06:14 blocker is over.** |
| partial judge directories | none — all 40 most recent judge dirs are at 495 rows; the 453–473-row `bnd2` residue was already deleted |
| empty-goal leakage | `empty_goal_leakage_check.json`: 15 tainted runs, 9 dependent artifacts, **3 live in a deliverable** (`clearharm_decomposition.json`, `qwen3_channel_test.json`, `section14_topical_asr.json` Qwen3 half). None of them is an input to this phase |
| judge provenance | `strongreject_rubric via poc_stage3.strongreject_scoring`; candidates `["openai/gpt-4o-mini","openai/gpt-3.5-turbo"]` tried in order with fallback. ⚠ **Which model answered a given row is not recorded and is not one model** (`judge_boombness.py:465`). Never attribute a score to gpt-4o-mini |

**Phase 0 gate: PASS.** Cleared for GPU/judge work at 17:20.

### 0.3 ⬆ Two Phase-0 discoveries that change the plan's sequencing

**(a) Credits are back, so Phase 1 is executable today.** The plan was written assuming Phase 1 was
blocked. It is not. Phase 1 moves to immediate execution.

**(b) There are SIX dose-matched L12 arms already generated, not two.** The follow-up log names only
`dd12a008` and `dd12a006`. A scan of every `project_out:12-12` run found a complete generated ladder,
all 495 rows, all `DONE`:

| run | α | intended realized removal fraction |
|---|---|---|
| `abL12_B_20260819_063539_2455409` | 1.00 | 0.820443 (the standard full-dose arm) |
| `dd12a03_20260823_040601_1736089` | 0.30 | 0.418426 |
| `dd12a02_20260823_035358_1732276` | 0.20 | 0.295359 |
| `dd12a015_20260823_034204_1728050` | 0.15 | 0.227673 |
| `dd12a01_20260823_031117_1718593` | 0.10 | 0.155884 |
| **`dd12a008_20260823_043816_1746076`** | **0.08** | **0.126020 — see C-1 below: this is ABOVE the L12 ceiling** |
| **`dd12a006_20260823_043816_1746077`** | **0.06** | **0.095500 — the only genuinely in-band arm at L12** |

This turns Phase 1B from a two-point underpowered test into a **seven-point dose–response curve at
one layer**, spanning the full arm down toward the control ceiling, at **zero additional GPU cost**
(two further points were generated to bracket the band properly — see C-1).
That is a strictly better instrument for the `DOSE_CAVEAT` than what the plan anticipated, and it is
the single highest-value thing available right now.

⚠ The realized fractions above are **nominal** (recomputed from `directions_fit_dev.pt` during the
08-23 audit, using removal = `0.820443 · (1 − (1−α)²)`). Phase 1B **must re-verify realized dose from
the run payloads**, not trust α — that is the plan's explicit instruction and the exact failure that
made the first four doses wrong.

### 0.4 Concurrency ownership

Two peer Claude sessions are alive (both idle at 17:19): `BOOMBNESS_D_SURFACE_FOLLOWUP
implementation` and `c-002-stateless-hare`.

⛔ **CORRECTED 17:24 — `91e30a62` is UNATTRIBUTED.** This file first recorded it as the follow-up
session's commit. That session replied that it is not theirs (their last commit was the 06:05
credits writeup), and it is not this session's either — this session has made exactly one commit,
`8bd07054`. So a **third actor** committed to the shared branch at 17:09:38. Its content (a
retraction-fingerprint guard experiment, 139 flags / 1 genuine, deliberately NOT wired into
`check_all`) is coherent and harmless, and its one genuine finding — that report §4b is built on the
readout R-6 withdrew — is real. But **nobody in contact owns it.** Treat the shared branch as having
an unreachable writer. Concretely: re-check `git log` before every commit, and never assume the tree
you read is the tree you last wrote.

**Protocol declared at 17:19 and messaged to the follow-up session:**
* This session owns SLURM submissions for this phase; every job id, its tree commit and its output
  dir go in §5 below.
* **No `scancel` by anyone without first verifying the exact tree the target job will execute** —
  correction C-1 in the follow-up log is the precedent (four jobs cancelled on a reason that was
  false by seventeen seconds).
* Commits are staged **by explicit path**, never `git add -A`, so no peer's in-progress file is swept.
* A peer that needs to submit should report its job ids here so they are recorded as theirs and not
  treated as strays.

**Peer accepted all four points at 17:23** and independently re-verified the credit restoration and
the empty queue rather than taking them on trust. It also reported one job of its own — recorded in
§5 as **776368 (peer-owned)** — and confirmed it deleted the six partial `bnd2_*` judge dirs
(453–473 of 495 rows) left by the credit failure. **Nothing in this phase may glob `bnd2_*`
expecting those partials; they are intentionally gone,** and that is the correct end state (a
partial dir flows through `load()` and produces a plausible number).

---

## 1. PRIMARY GOAL OF THIS PHASE

Not to rescue the old hypothesis. To determine **what the surviving mechanism actually is**, and
whether this chain can be established cleanly:

```
demonstrations → retrieval / remapping mechanism → internal state / refusal interaction → harmful behaviour
```

Two questions dominate:

1. **Is the demonstration-retrieval mechanism (G1/G3) causally necessary for the behavioural
   jailbreak itself** — measured on behavioural prompts, with behavioural outcomes?
2. **Does `d_surface` have any causal specificity beyond intervention dose?**

Only a mechanism that passes strong causal *and* predictive gates earns a GCG/MAC objective later.

---

## 2. THE PLAN — phases and decision gates

### PHASE 0 — reproduction, audit, clean start
**Status: ✅ COMPLETE, gate PASS (§0.2).**

### PHASE 1 — finish the already-generated pending experiments
Highest priority: the generations exist, only judging is missing, and credits are back.

**1A — Experiment 7 random-control band.** Judge `e7rnd01/02/03` (three matched `random:add:8-8:0.5`
draws at seeds 20260901/02/03) and ask whether the exp-7 directional effect survives a real
between-seed band rather than one draw.
**1B — Dose-matched `d_surface` arms.** Judge the full seven-point L12 ladder (§0.3b) and re-verify
realized dose from the payloads. Tests the `DOSE_CAVEAT` directly.
**1C — Session-matched baseline/control cleanup.** Everything in 1A/1B is judged in **one session
against one baseline**, producing a canonical artifact with consistent populations.

#### 🚦 Decision Gate E7 (1A)
PASS only if the effect (i) survives the full control band, (ii) has a stable sign, (iii) is not
driven mostly by one pathological control draw, (iv) remains meaningful under the pre-registered
multiplicity family, and (v) is not explained by generic perturbation magnitude.
Otherwise: label **exploratory / null** and move on.

#### 🚦 Decision Gate DOSE (1B)
* If the effect **vanishes** at realized dose ≤ 0.13 → much of the specificity story was dose-driven.
  A clean, publishable negative.
* If it **persists** → direction identity matters independently of dose, and the standing
  `DOSE_CAVEAT` is answered rather than acknowledged.
* Pre-registered: these arms are **underpowered**; report point estimate + CI + the dose–response
  shape, **not** a bare verdict. Do not overclaim a null.

### PHASE 2 — behavioural-prompt demonstration-retrieval knockout  ← the key new experiment
Close the G1/G3-vs-behaviour gap. Arms, on matched **behavioural** natural-doublespeak prompts:

| arm | intervention | role |
|---|---|---|
| A | baseline | reference |
| B | demonstration **text deletion** | behavioural ceiling |
| C | **full demo-block attention knockout** (the G3 arm that worked) | primary mechanistic arm |
| D | matched random attention knockout (same edge count) | matched control |
| E | sparse top-ranked edges/heads | tests whether redundancy holds behaviourally |
| F | bottom-k / random sparse | matched sparse control |

Outcomes on the **same rows**: StrongReject continuous, binary ASR, refusal rate, refusal→compliance
and compliance→refusal flips, answer length, topicality, comprehension. **Where feasible, preserve
the G3 readout on the same rows** so the row-level question can be asked directly: *does destruction
of the retrieved binding predict destruction of attack behaviour?*

Sampling: ≥ 20 independent examples per meaningful comparison (far more for judge-based ASR),
family-disjoint splits, multiple domains, pooled **and** clustered estimands reported separately.
Log the actual sample composition — a count is not a description.

#### 🚦 Decision Gate RETRIEVAL (2D)
* **Strong positive** — knockout destroys the internal mapping **and** lowers doublespeak ASR toward
  a meaningful fraction of the text-deletion ceiling, preserves unrelated capability better than
  deleting the text, and matched controls are substantially weaker → first clean chain
  `demonstrations → retrieval → jailbreak behaviour`. Headline result.
* **Negative but informative** — mapping disappears, ASR unchanged → representation ≠ behaviour at a
  deeper mechanistic level. **Publish it; do not hide it.**
* **Failed intervention** — neither moves → first prove the pathway was actually cut (positive
  control) before interpreting any null.

### PHASE 3 — connect retrieval to refusal
Composition on matched populations: `baseline` / `retrieval knockout` / `refusal removal` /
`retrieval knockout + refusal removal`, to separate
*retrieval → refusal → behaviour* from *parallel channels* from *refusal-independent*.
Measure refusal-direction projection by layer, and whether refusal change is larger among rows that
flip. **Do not infer mediation from correlation alone.**

### PHASE 4 — Llama vs Qwen3
Run the strongest Phase-2 experiment on both `meta-llama/Llama-3.1-8B-Instruct` and `Qwen/Qwen3-14B`.
**Choose external sets by measurable baseline headroom** — Qwen3 complies with only **0.8% of
AdvBench (4/495)** vs 13.4% of ClearHarm, and an intervention cannot be measured against a floor
(N13). **Always report baseline compliance beside every delta** (N14).
Question: *do the two models jailbreak through the same semantic-remapping mechanism but gate it
through different behavioural channels?*

### PHASE 5 — fix the direction-vs-dose identification problem
Build a **new identification bank** whose cell-mean covariance has multiple comparable components
instead of one dominant PC1. Multiple codewords × multiple harmful concepts, clean 2×2, no grammar
or tokenization asymmetries (no repeat of `a apple`), family-disjoint splits, mandatory tokenization
audit on **both** models before any expensive run.

#### 🚦 Bank acceptance gate
Do not proceed to large causal runs unless PC1 does **not** dominate the cell-mean span, multiple
identified directions have **comparable attainable doses**, and the bank passes
tokenization/alignment/grammar audits. The point is *same dose, different direction*.

### PHASE 6 — re-test concept generality properly
Only on the improved bank. Within-concept-across-codeword vs within-codeword-across-concept
similarity, split-half ceilings, cross-pair causal transfer, off-bank and behavioural transfer.
**Neutral names (`d_surface_pairX`) until the invariance tests pass.**

### PHASE 7 — only then, a new objective
Six independent gates: **measurement · prediction · causality · specificity · transfer · optimization
direction**. The promising candidate is a *retrieval-strength* or *retrieval-driven refusal
suppression* quantity, **not** raw codeword-token `d_surface`. Reuse `external_repos/interp-jailbreak`
and our prior GCG/MAC infra rather than rewriting.

---

## 3. EXPERIMENT STATUS BOARD

Legend: ⬜ not started · 🔬 running · ✅ complete · ⛔ failed/retracted · ⏸ blocked

| id | phase | experiment | status | gate |
|---|---|---|---|---|
| P0 | 0 | reproduction + audit + guard suite | ✅ PASS | — |
| E7-BAND | 1A | exp-7 random control band (3 draws) | 🔬 judging (**peer job 776368**) | Gate E7 |
| DOSE-L12 | 1B | **nine-point** L12 dose ladder | 🔬 generating 776391/776392 | Gate DOSE |
| SESSION | 1C | one-session canonical control artifact | ⬜ waits on 776391/776392 | — |
| RETR-BEH | 2 | behavioural demo-retrieval knockout | 🔬 **unblocked** — hook fixed + 10/10 tests; wiring next | Gate RETRIEVAL |
| RETR-REF | 3 | retrieval × refusal composition | ⬜ | — |
| XMODEL | 4 | Llama vs Qwen3 matched | ⬜ | — |
| BANK2 | 5 | new non-PC1-dominated bank | ⬜ | Bank gate |
| CONCEPT | 6 | concept generality on BANK2 | ⬜ | — |
| OBJ | 7 | new objective | ⬜ | 6 gates |

---

## 4. RUNNING JOBS

*(ownership: this session unless marked otherwise)*

| job id | owner | what | submitted | tree commit | output | status |
|---|---|---|---|---|---|---|
| **776368** | **peer** | `run_band2_judge.sh` — judges base + e7rnd01/02/03 + dd12a008 + dd12a006 in one session (6 × 495 = 2,970 calls) | 17:16 | `91e30a62` | `outputs/boombness/judge/bnd2_*` | RUNNING |
| **776391** | this | generate `d_surface:project_out:12-12:**0.045**` on AdvBench-495 (tag `dd12a45`) | 17:26 | `91e30a62` | `outputs/boombness/score_behavior/dd12a45_*` | PENDING |
| **776392** | this | generate `d_surface:project_out:12-12:**0.03**` on AdvBench-495 (tag `dd12a3`) | 17:26 | `91e30a62` | `outputs/boombness/score_behavior/dd12a3_*` | PENDING |
| **776397** | this | **Gate E7 in ONE session**: base + dS50 + rnd50 + rnd75 + e7rnd01/02/03, 7 × 495 (`scripts/judge_p1a.sh`) | 17:34 | `50e5d7e8` | `outputs/boombness/judge/p1a_*` | RUNNING |
| **776437** | this | **Phase 2 smoke, arm C** — `demo_all:attn_knockout:18-19:1.0`, 8 prompts | 18:01 | `54c66143` | `.../score_behavior/p2smokeC_*` | PENDING |
| **776438** | this | **Phase 2 smoke, arm P** — `allpast:attn_knockout:18-19:1.0` (positive control), 8 prompts | 18:01 | `54c66143` | `.../score_behavior/p2smokeP_*` | PENDING |

---

## 5. SLURM JOB LEDGER

Every job submitted by this phase, with the commit its tree will execute.

*(appended as jobs are submitted)*

---

## 6. RESULTS

### ★★★ R-A (17:42) — PHASE 2 WAS UNRUNNABLE, AND THE FAILURE WOULD HAVE BEEN SILENT

**Question.** Can the G3 demonstration-block attention knockout be run *under generation* on
behavioural prompts, so that the retrieval mechanism can be tied to jailbreak behaviour?

**Answer: NO, not with the existing code — and running it anyway would have produced a
clean-looking, publishable, WRONG null.** Five independent audits converged on the same two
defects in `doublespeak_causality/pair_common.py:463-476`.

**Defect 1 — the knockout is prefill-only.** `AttentionKnockout` addresses query rows by
**absolute prompt position**. Under KV-cached decoding the additive mask has shape
`[1, H, 1, kv_len]`, so `am.shape[2] == 1` and the guard

```python
if qp >= am.shape[2]: continue
```

**skips every absolute query position on every decode step.** The block applies during prefill and
then switches itself off for the entire generation. This is asserted as *intended* behaviour by the
existing test (`tests/test_attnknockout_synthetic.py:185-192`: "a query index past the current seq
(e.g. a decode step) is skipped, not an error") — correct for the teacher-forced readout it was
built for, fatal for a behavioural experiment.

**Defect 2 — the causality guard compares incompatible index spaces.** `if 0 <= kp <= qp` tests an
**absolute** key index against a **cache-local** query index (which is `0` on a decode step), so
even a query row that survived defect 1 would reject every demonstration key.

**Why this matters more than an ordinary bug.** The run would still emit rows, still report
`n_edges_cut`, still exit 0, and yield *"full demonstration-block knockout does not change
jailbreak ASR."* That reads as the plan's "negative but informative" branch — representation ≠
behaviour at a deeper mechanistic level — and it would be a statement about **a hook that turned
itself off after the first generated token.** This is the repo's documented
`feedback_absolute_position_index_bug` class, which has now landed three times.

**Two further blockers found by the same audits:**
* `src/boombness/surgical_knockout.py` **has no generation path at all** — no `.generate`, no
  `gens.jsonl`; it terminates in `signals.string_option_readout`, teacher-forced with
  `use_cache=False`. The only `.generate` in `src/boombness` is `score_behavior.py:646`.
* `score_behavior.py:468` **hardcodes `attn_implementation="sdpa"`**, under which a custom 4-D
  additive mask is discarded without error. A knockout run under SDPA is not a weak result, it is a
  **void** result.

**And the reference repo cannot help.** `external_repos/interp-jailbreak` (arXiv 2506.12880) is
**entirely observational** — a full grep for `hook_fn` / `add_hook` / `run_with_hooks` returns
nothing. There is no causal-intervention machinery to reuse. We build it.

**FIX IMPLEMENTED (17:43).** New class `AllQueryAttentionKnockout` in
`doublespeak_causality/pair_common.py:495`, alive at prefill **and** decode. The index algebra:
KV-cache columns are absolute, so `kp` indexes `am[..., kp]` directly; query row `r` is absolute
position `past + r` with `past = am.shape[3] - am.shape[2]`, so the first causally-blockable row is
`lo = max(0, kp - past)` and every row from `lo` on is masked. At prefill this reduces to the lower
triangle; at decode `lo == 0` whenever `kp <= past`, which is the case that matters.

It carries **liveness instrumentation** (`n_decode_forward`, `n_decode_edits`) precisely so that a
caller can *prove* the mask fired during generation instead of assuming it. A run whose
`n_decode_edits` is 0 is void and must refuse to report.

`AttentionKnockout` is **deliberately left untouched** — `surgical_knockout.py` and every committed
G1/G3 artifact depend on its skip semantics, and changing it in place would silently re-score
published results.

**Tests: 10/10 pass** (`doublespeak_causality/tests/test_allquery_attnknockout.py`), including
`test_old_class_is_dead_at_decode_THIS_IS_THE_REGRESSION_GUARD`, which asserts the **pre-fix**
class's failure directly — the repo's standing rule that a guard must ship with a test that fails
the old code. The pre-existing suite still passes 17/17, so G1/G3 are not disturbed.

**Status:** Phase 2 is now *buildable*. It was not, ninety minutes ago, and nothing in the written
plan would have revealed that — only reading the hook did.

---

## 7. BUGS / RETRACTIONS / CORRECTIONS (this phase)

### ⛔⛔ C-2 (18:06) — MY OWN DOSE CLAIM IS HALF REFUTED: "dose-matched" IS METRIC-DEPENDENT

An adversarial re-derivation (instructed to default to refuting me) **confirmed** the arithmetic of
C-1 and then **broke the conclusion I drew from it**. Both halves matter.

**CONFIRMED, and upgraded from extrapolation to measurement.** The L12 control band really is
**0.0593825775943842 (angle23) – 0.120174685705822 (angle11)**, the ARM really is
**0.820442884781259**, and "≤ 0.13" really is L10's `0.13155342189253746`. The removals I had
*extrapolated* were re-derived by applying the actual hook algebra to the actual cell means and
agree to **5e-8**: α 0.08 → **0.126020091450253**, α 0.06 → **0.0954995141712899**. The hook is
linear (`h → h − α(h·u)u`), so `frac·(1−(1−α)²)` is exact, not an assumption. **dd12a008 is above
the L12 ceiling and dd12a006 is inside it — that stands.** A bonus: the L12 complement's *geometric*
ceiling is 0.120197429500161, so the sampled 24-angle max is **99.98%** of the attainable maximum —
at L12 the ceiling is a hard bound, not a sampling artifact.

**⛔ REFUTED — "α 0.0459 is mid-band" is wrong.** 0.073588 sits above only **8 of 24** controls: the
**33rd percentile**, i.e. low-band. The true median and range-midpoint coincide at
**0.0897786**, which is **α = 0.056298**.

**⛔⛔ AND THE DEEPER PROBLEM, which neither C-1 nor the follow-up log saw.** `dose_cellmean_frac`
is a **variance** (squared) metric. At α = 1 the norm metric is its square root — a monotone
transform — so every rank and isotonic argument in this repo has been **metric-invariant by
accident**. **Partial α is the first place that invariance breaks**, because variance removed goes
as `1−(1−α)² ≈ 2α` while the perturbation *norm* the model actually experiences goes as `α·|proj|`.
Measured at L12:

| metric | 24 controls span | arm α=0.08 | arm α=0.30 | α needed to match the band |
|---|---|---|---|---|
| **cell-mean variance removed** (the repo's `dose`) | 0.0594 – 0.1202 | **0.1260** | 0.4184 | **0.0369 – 0.0699** |
| **cell-mean spread removed, Frobenius NORM** | 0.2437 – 0.3467 | 0.0725 | **0.2717** | **0.2690 – 0.3827** |
| fraction of uncentred activation norm removed | 0.1360 – 0.2198 | — | — | 0.3213 – 0.5193 |

**The arm-versus-control comparison — the entire point of dose matching — moves by roughly an order
of magnitude in α depending on which metric is chosen.** Worse, the third metric is not even
monotone with the first: it re-ranks the controls among themselves (argmax becomes angle15, not
angle11). Ordering *within* the ladder is safe (all three are monotone in α); only the
arm-vs-control matching flips.

**DECISION D-7 — pre-register both metrics, and note the ladder already brackets both.** This is
pre-registered now, before any of these arms has an ASR (verified: **none of the six `dd12a*` runs
has a judge run**, so there is nothing yet to rank and nothing to select on):

* **Variance-matched arm: `dd12a006`** (0.0955, inside 0.0594–0.1202) — and α **0.0563** submitted
  to sit exactly at the band median 0.0898.
* **Norm-matched arm: `dd12a03`** — α 0.30 gives norm 0.2717, which is **already inside** the norm
  band 0.2437–0.3467. It was generated as a "too high" throwaway and turns out to be the
  norm-matched point. α **0.38** submitted for the band's upper edge.
* **Gate DOSE will be reported under BOTH metrics, separately labelled, and a disagreement between
  them is itself the finding** — not something to resolve by choosing the flattering one.

⚠ Two provenance defects found in passing: the six `dd12a*` runs record **only α** — no dose, no
cosine, because `frac_cellmean_spread_removed` is emitted on the in-subspace control branch only —
and every one of them is stamped `dose_unit = "gap (alpha=1 == one diff-of-means) for mode=add"`,
boilerplate written unconditionally and **inapplicable to `mode=project_out`**. A reader could take
α for a gap-unit dose.

### ⛔ P-0 (17:45) — THE THIRD WRITER SWEPT MY IN-PROGRESS FILES INTO ITS COMMIT

At **17:40:43** the unattributed writer (§0.4) committed `9672cf04`, "the figure I promoted into a
banner had no script behind it" — a commit about the §4b recompute. It contains **eight** files, two
of which are mine and have nothing to do with its subject:

* `scripts/judge_p1a.sh` (61 lines) — the Gate E7 judging driver I wrote at 17:36
* `src/boombness/slurm/run_p1a_judge.sh` (14 lines) — its sbatch wrapper

That is a broad `git add -A`. **Verified consequences:** my files were committed *intact* —
`git diff HEAD` for both is empty and both still pass `bash -n` — and job 776397 had already read
the script at launch, so nothing running was affected. **Unverified-but-real risk:** had the sweep
landed sixty seconds earlier it would have committed a half-written script, and a SLURM job reading
the tree at runtime would have executed it. That is the precise hazard this phase's own protocol
(§0.4, "stage by explicit path, never `git add -A`") exists to prevent, arriving from the direction
the protocol could not defend against — someone else's sweep, not mine.

**Standing mitigation for the rest of this phase:** commit own work promptly to minimise the window;
`git log` immediately before every commit (HEAD moved twice in 35 minutes); and after any commit,
`git diff HEAD` the files just written to confirm the committed bytes are the intended bytes. The
provenance cost is already paid and not recoverable: my Gate E7 driver is attributed to a commit
message about §4b.

### ⚠ P-1 (17:43) — PROCESS: I twice came close to cancelling a healthy job on inference

Job 776368 (not mine, now unowned) sat at **0 bytes of log and 0 RunDirs for 22 minutes**. Against
the documented signature *"a 0-byte log under `set -e` means HANG, not nothing ran"*, that looked
decisive, and I drafted a cancellation.

**It was wrong, twice over.** (a) `scripts/judge_band2.sh` has **no progress echo at all** — its
only `echo` is *after* `wait`. A 0-byte log is that script's expected behaviour until it finishes;
my own job looked different solely because I added echoes to mine. (b) I then fell back on "0
RunDirs = never started" — but my own healthy job also showed 0 RunDirs at the same point, so the
comparison proved nothing.

Both times the tell was that I was reading a **proxy** (log bytes) shaped by a property of the
*script* rather than of the *job*, and treating a difference between two scripts as a difference
between two jobs. That is the same shape as the FM1 dead-guard family: addressing something by an
incidental property instead of by identity.

**776368 was left running.** It is expected to produce a genuine cross-session replicate of
`dd12a008`/`dd12a006`, which is useful rather than wasteful. C-1 in the follow-up log — four jobs
cancelled on a reason false by seventeen seconds — is the precedent this avoided repeating.

### ⚠ C-1 (17:25) — "the controls' ≤0.13 band" is a CROSS-LAYER maximum, and it is the wrong comparator at L12

The standing framing — repeated in the follow-up log, in the peer's message, and in the first draft
of §0.3b of this file — is that the in-subspace controls remove **≤ 0.13** of the cell-mean spread,
so an arm at 0.126 or 0.095 is "inside the control band". **0.13 is the maximum over all four
layers.** Recomputed per layer from `insubspace_null_full24.json` `dose_cellmean_frac` (24 controls
each):

| layer | ARM removal | control min | **control max** | arm/max |
|---|---|---|---|---|
| L6 | 0.876824 | 0.043145 | 0.080031 | 10.96× |
| L8 | 0.840201 | 0.045659 | **0.114140** | 7.36× |
| L10 | 0.811446 | 0.057001 | **0.131553** | 6.17× |
| **L12** | **0.820443** | **0.059383** | **0.120175** | 6.83× |

The 0.13 figure is L10's. **At L12, where the dose-matched arms actually run, the control band is
0.059383 – 0.120175.** Consequences for Gate DOSE:

* `dd12a008` (α 0.08, removal **0.126020**) is **above** the L12 control ceiling by 1.05×. It is
  *near*-matched, not matched. It cannot carry a clean "same dose, different direction" claim.
* `dd12a006` (α 0.06, removal **0.095500**) **is** inside the L12 band, at roughly its midpoint.
  **This is the decisive arm**, and it is the one the log treated as the throwaway "below the band"
  point.
* Nothing yet sits at the band's **median** or **below** it. Solving `removal = 0.820443·(1−(1−α)²)`
  gives α **0.0459** → 0.0736 (mid-band) and α **0.0310** → 0.0500 (below the band's minimum).

**Action taken:** submitted jobs **776391** (α 0.045) and **776392** (α 0.03) so the ladder brackets
the L12 control band on both sides instead of approaching it from above only. Cost: two 495-prompt
generations, no judging until they join the same session as the rest.

⚠ This correction does **not** overturn any published result. It refines the design of a test that
has not been read out yet — which is the only time a correction is cheap.

---

## 8. DECISIONS AND WHY

**D-1 (17:20) — Phase 1 runs first and runs today, not later.** The plan assumed judging was blocked.
It is not (§0.2). Judging already-generated runs is zero-GPU, answers two standing gates, and
produces the session-matched baseline every later comparison needs. Deferring it to start Phase 2
would leave five completed GPU runs unused and Phase 2's controls unmatched.

**D-2 (17:20) — judge the full seven-point L12 ladder, not the two arms named in the log.** §0.3b.
Same cost class, strictly more information, and it converts an underpowered two-point test into a
dose–response curve that can distinguish "the effect decays with dose" from "the effect vanishes at
the control ceiling". These two hypotheses are not separable with two points.

**D-3 (17:20) — one judging session for all of Phase 1, against one baseline.**
`ab_base_20260818_185458_3888976` is the baseline the exp-7 arms already used. Judging the new
controls, the dose ladder, the full-dose reference arm and the baseline in a single session removes
the cross-session confound that produced the L6 reversal and the F-3 retraction. This *is* Phase 1C,
executed as part of 1A/1B rather than as a separate later cleanup.

**D-4 (17:20) — smoke before sweep.** One arm at `--limit 8` first, inspect the rows, verify goal
status and row counts, then launch the full manifest. Required by the engineering rules and cheap.

**D-5 (17:26) — do NOT duplicate peer job 776368; complement it.** The peer submitted the exact 1A
manifest before this file existed. Re-running it would burn 2,970 duplicate judge calls and create
colliding tag dirs. This session instead owns the **ladder completion**: the four higher-dose arms
(α 0.10/0.15/0.20/0.30), the full-dose reference (`abL12_B`, α 1.0), the two new bracketing arms
(α 0.045/0.03), and a re-judge of α 0.08/0.06 **inside this session** so the ladder is internally
session-matched. The re-judge is deliberate duplication of two arms, for two reasons: (i) a ladder
whose points come from two judging sessions is exactly the cross-session confound that produced the
L6 reversal, and (ii) it yields an independent judge test–retest on the two arms that decide Gate
DOSE, which is worth 990 calls on its own.

**D-6 (17:26) — bracket the control band before reading it out.** See C-1. A dose-matching test whose
arms all sit above the control ceiling cannot answer "same dose, different direction"; it can only
answer "slightly less dose". Two generations fix that for ~40 GPU-minutes, and they were submitted
before any judging spend, so no result is contaminated by the decision.

---

## 9. OPEN QUESTIONS

1. Does the exp-7 directional effect survive a real 3-draw control band? *(Gate E7, in flight)*
2. Does `d_surface` removal still move behaviour at realized dose ≤ 0.13? *(Gate DOSE, in flight)*
3. Is demonstration retrieval causally necessary for behavioural jailbreak? *(Phase 2)*
4. How much of any retrieval effect is mediated by refusal? *(Phase 3)*
5. Do Llama and Qwen3 share the mechanism but differ in the behavioural gate? *(Phase 4)*
6. Can a bank be built that separates direction identity from removed variance? *(Phase 5)*
7. Does anything generalise across concepts/codewords? *(Phase 6)*
8. Is there a justified monotonic causal objective worth optimizing? *(Phase 7 — if no, say so)*

---

### R-B (18:00) — the Phase 2 population is defined, balanced, and family-disjoint

The filter, now expressible because `score_behavior.py` grew `--conditions` / `--bank-blocks` /
`--n-examples` / `--expect-n`:

```
query_kind == "behavioral" AND condition == "natural_doublespeak"
AND bank_block in {core2x2, core2x2_slot3} AND n_examples in {1,2,4,8}
```

**n = 96**, and it is unusually clean:

| | |
|---|---|
| distinct families | **96** — one row per family, so family-disjoint *by construction*; sibling-family leakage (the R-18 defect) cannot recur here |
| domains | 6 × **16** each, exactly balanced |
| splits | dev 48 / heldout 48 |
| demo counts | 24 each at `n_examples` 1 / 2 / 4 / 8 |
| `demo_block` integrity | **0** rows missing it; **0** rows where it fails to appear exactly once in `full_prompt` |

Deliberately excluded: `n_examples ∈ {0, 16}` (0 is demo-free and structurally ineligible; 16
reintroduces cross-slot demo sharing) and every manipulation block (`strength`, `consistency`,
`position`, `role_style`, `families`) — the two halves of R-18.

⚠ **Power, stated before the result rather than after.** At a baseline ASR near 0.19 this is ~18
successes over 24 informative clusters. A knockout-to-floor effect is detectable; a 25% partial
effect is not. **Pre-registered: a non-significant result here is reportable only as "we can
exclude a reduction larger than X", never as "the pathway is not causal for behaviour."**

---

## 10. CANONICAL ARTIFACTS OF THIS PHASE

| artifact | produced by | holds |
|---|---|---|
| `outputs/boombness/judge/p1a_*` | job 776397 | Gate E7, one session, 7 arms |
| `outputs/boombness/judge/bnd2_*` | job 776368 (orphan) | independent cross-session replicate of dd008/dd006 |
| `.../score_behavior/p2smoke{C,P}_*` | jobs 776437/776438 | Phase 2 liveness smoke |

---

## 11. NEXT ACTIONS

1. Smoke-test the judge on one arm (`--limit 8`), inspect output. *(in progress)*
2. Submit the single-session Phase 1 judging manifest to `cpu-killable`.
3. While judging runs: build the Phase 2 behavioural knockout arm list by reading
   `src/boombness/surgical_knockout.py` and confirming which arms are reusable unchanged.
4. Analyse 1A/1B, decide Gates E7 and DOSE, write results into §6.
