# Boombness / `d_surface` sprint — Part II, 2026-08-23 16:07 → 2026-08-24 23:05

**Project:** Tel Aviv University MSc research (Omer Yosef; advisor Mahmood Sharif; with Matan Ben-Tov).
Mechanistic interpretability of jailbreak / prompt-injection mechanisms.
**Repo:** `first_poc/teza_first_poc_with_mahmood`, branch `behavioral-causality-sprint`.
**Window:** first commit after Part I `2ff8d24a` (2026-08-23 16:38:12) → HEAD `8c83c8f3`
(2026-08-24 23:04:57). **113 commits.**

**What this document is.** A self-contained account of the work done after
`reports/SPRINT_SUMMARY_2026-08-16_TO_08-23.md` (Part I) closed at HEAD `016f3c98`, 2026-08-23 16:07.
It is written for a reader — human or LLM — with **no prior knowledge of the project**: §1 restates
everything from Part I that is needed to follow §5 onward. Every number is quoted at the precision it
is stored at, with its producing artifact named.

**Verification status of this document.** Written 2026-08-24/25 by re-deriving figures from the
committed artifacts and source rather than from the project's own prose. **361 individual checks**
were run across twelve claim families, each recomputing the number from the `.json` / `.pt` artifact
or the source file: **338 MATCH, 14 MISMATCH, 9 UNVERIFIABLE**. Every mismatch was then handed to an
independent adversarial re-derivation instructed to default to refuting the verifier: **5 were
refuted** (the log was right, the verifier looked in the wrong place), **1 was superseded** (the log
had already retracted it), and **8 were upheld as genuine defects**. Those 8, the 9 unverifiables,
and a further set of issues nobody had asked about are in **§11** — they are *new*, not copied from
the project's own correction registry. The six-guard deliverable suite `check_all.py` was executed
live at HEAD and **exits 0 (all six pass)**.

---

## ⛔ POST-PUBLICATION CORRECTION — read before §6.8 or §13

**This document was written at `8c83c8f3` (2026-08-24 23:04). Its headline result was retracted 48
minutes later**, at `9b9adddc` (23:35), by the project's **eighteenth** correction.

> **C-18 / REVIEW-8 retracts R-BD.** All ten populations use the **identical 96 `prompt_id`s**, so the
> `pool × domain` k=18 unit is a fully crossed **3 × 6 table** on one shared prompt set, in which
> **62.1 % of the spread is two main effects counted 3× and 6× over** (pool main effect SS 0.10102 /
> df 2 / 30.2 %; domain main effect SS 0.10655 / df 5 / 31.9 %; interaction 37.9 %). **Both marginals
> include zero** — k=3 pool means **[−0.3043, +0.1516]**, k=6 domain means **[−0.1649, +0.0121]** — and
> only their product excludes it. *"That is the signature of double-counting, not of evidence."* The
> correct crossed random-effects interval is **[−0.2796, +0.1268]** at **df 2.53**.
>
> Three further defects were confirmed and fixed in the same correction: the headline run used
> `--thresholds 0.5` only, and **at 0.75 the CI includes zero** ([−0.1158, **+0.0012**]); **every**
> single leave-one-out drop kills the exclusion (drop bomb, knife or gun, or Llama-only — only
> Qwen3-only survives); and the `_T` table had **no df=17** entry, so the k=18 run used an
> anticonservative fallback (2.1012 vs 2.10982).

**What this changes in this document.** §6.8 and §13 quote R-BD as *"the first calibrated cluster test
of magnitude that excludes zero."* **That statement is withdrawn.** The correct position is **C-17's**,
and it is the one this document should be read as ending on:

> **The direction is well supported** — 113 down-flips against 30 up over 10 populations
> (p = 1.577e-12), a both-arms-EOS control of 30/1 (p = 2.98e-08), replicating on the high-headroom bank
> of both models (−0.1771 Llama, −0.2083 Qwen3), with no fitted direction anywhere so no dose confound
> is possible. **No calibrated cluster test of MAGNITUDE excludes zero.**

**Everything else in this document stands**, including all 361 verification checks in §11 — the
verification was run against the artifacts, and the artifacts are unchanged. Note that §11.2 flagged
R-BB's within-cluster sd of 0.0626 as not reproducing (the obvious reading gives **0.0878**);
**C-18's S6 confirms 0.0878 independently**, so the depth penalty is 7.1 %, not 3.6 %. §11.3 item 1
(the still-live `asr_<bank>` model collision and `n_independent_pools = 5`) was **confirmed as C-18's
S4 and fixed** in `059e819f` — `n_independent_pools` now reads 3, and the artifact carries ten
model-keyed ASR rows.

### And a second correction, one hour later: **R-BE — the axis this window spent three phases adding was the wrong axis**

Committed `7838dcd2` (2026-08-25 00:21). After C-18 the only defensible unit is the **domain marginal**:

| domain | Δ over all 10 populations |
|---|---|
| `game_manual` | **−0.2562** |
| `news_report` | −0.0938 |
| `city_bridge` | −0.0875 |
| `instructional` | −0.0750 |
| `farm_storage` | −0.0063 |
| `lab_safety` | **+0.0000** |

**k = 6, mean −0.0865, sd 0.0927, Cohen's d = 0.933, CI upper +0.0108 — includes zero.** Holding that
mean and sd, the projection is **8 domains → −0.0090 (excludes zero)**, 10 → −0.0202, 12 → −0.0276.

> **The binding constraint was always the number of DOMAINS — not banks, not pools, not models, not
> concepts.** Phase 8 had already stated it in its own words (*"the sign-flip test operates on domain
> clusters, and there are 6, so the p-floor is 2/2⁶ no matter how many prompts each domain holds"*),
> and Phases 8, 9, 10 and 10b then added four banks, a third pool, a second model and a fourth
> concept — **all of them reusing the same six domains.** C-11, C-15 and C-18 killed the pool, model
> and pool×domain axes for exactly this reason.

⚠ **Carry the author's own caveat:** the projection holds mean and sd fixed while the effect is
concentrated (`game_manual` −0.2562 against a −0.0865 mean; `lab_safety` exactly 0.0000). New domains
could be `lab_safety`-like, raising sd as they lower the mean. **"8 domains" is the optimistic read, not
a guarantee.**

The untried route, and it is cheap: `src/boombness/demo_pools.py` takes its domain list from a
module-level `DOMAINS` dict (~line 60) and records it in `_meta.domains`, so regenerating pools at
8–10 domains and rebuilding one bank per pool is an ordinary bank-generation job.

**Successor phase:** `external_md/DEMONSTRATION_RETRIEVAL_BEHAVIORAL_CAUSALITY_NEXT_PHASE_PLAN_AND_PROGRESS.md`
opens against the corrected state and carries R-BE into its Phase-4 decision.

---

**Primary source for this window:** `external_md/BOOMBNESS_DSURFACE_NEXT_PHASE_PLAN_AND_PROGRESS.md`
— 6,029 lines, 363,233 bytes, 117 `###` sections, **56 distinct result ids (`R-A` … `R-BD`)** and
**17 corrections (`C-1` … `C-17`)**, newest-first, opened 2026-08-23 17:20. It was touched by **97 of
the 113 commits**.

---

## 1. What you need to know from Part I

The sprint set out to turn a discovered weakness into a **GCG/MAC optimization objective**. The
hypothesis: in Doublespeak-style prompts a benign surface token (`carrot`) acquires a hidden
representation that is increasingly `bomb`-like; measure that "Boombness" scalar, show it predicts
attack success, show removing it surgically lowers ASR, then optimise a suffix that maximises it.

**The measurement instrument** is a 2×2 prompt design over one codeword and one harmful concept:

| | codeword `carrot` | concept `bomb` |
|---|---|---|
| **harmful context** | A: `natural_doublespeak` | C: `direct_harmful` |
| **benign context** | B: `benign_literal` | E: `concept_in_benign_ctx` |

Fitting on the four cell means yields `d_surface` (the surface-identity axis — the object of the
sprint), plus `d_context`, `d_naive`, `d_inter`. Interventions are expressed as
`name:mode:lo-hi:alpha`, e.g. `d_surface:project_out:12-12:1.0` removes the component along
`d_surface` from every position at layer 12.

**By 2026-08-23 16:07 the chain had broken at every link:**

* **G2 retracted** — `d_surface` does not predict attack success. The published n=234 correlation
  (+0.2618, p 0.0005) collapsed to −0.0518 (p 0.658) on a clean sample; the published sample was 31%
  sibling families sharing demonstrations.
* **G4 is a directional null** — steering *both* signs of `d_surface` suppresses ASR. There is
  nothing to optimise toward. **The GCG objective was never built, and should not be.**
* **The surviving effect runs backwards:** *removing* `d_surface` **raises** ASR on held-out AdvBench
  (+0.0424 at L8, 21 net flips of 495), localized to a band ≈ L6–L14 — but it is an order of
  magnitude smaller than the refusal channel (+0.2061 for refusal removal alone), and it is
  **dose-confounded**: `d_surface` is essentially PC1 of the cell-mean span (cos 0.9998–1.0000),
  removing 0.81–0.88 of the cell-mean spread while every in-subspace control removes ≤ 0.13, a 6–11×
  gap. Direction identity could not be separated from removed variance **as a matter of geometry**.
* **E12 retracted in full** — no transfer to a second concept. The object is
  `d_surface_carrot_bomb`, not "a bombness direction".
* **What *is* established:** **G1** — the codeword's meaning lives in the *demonstration block*, not
  in the codeword token (`demos_only|L18` transplant recovers +0.6887 of span; `query_only` moves the
  wrong way). **G3** — that retrieval is attention-carried and massively redundant: cutting all
  demonstration-block attention edges recovers **75.15%** of the text-deletion ceiling at 81,706.67
  edges cut, while sparse top-k knockout does nothing.
* **Plan §18 label: C, amended** — a refusal-only story with a second small channel that **inverts on
  Qwen3-14B** (there `d_surface` removal at L11 gives +0.3810 while refusal removal does nothing).

**The gap Part I named as the single cleanest next experiment:** G1/G3 are measured on
`semantic_one_word` readout prompts; the ASR claims are on `behavioral` prompts. **Nobody had ever
knocked out the retrieval pathway and measured jailbreak behaviour on the same rows.** Part I also
prescribed the fix for the dose problem: *"the next bank must not be PC1-dominated."*

**This window does both.** That is what it is for.

**Two models throughout, no third family:** `meta-llama/Llama-3.1-8B-Instruct` (32 blocks) and
`Qwen/Qwen3-14B` (40 blocks, `enable_thinking=false`), both bfloat16. **Judge:** `strongreject_rubric`
via `poc_stage3.strongreject_scoring`, candidates `["openai/gpt-4o-mini","openai/gpt-3.5-turbo"]`
tried in order with fallback; **which model answered a given row is not recorded and is not one
model** (`src/boombness/judge_boombness.py:465-471` says so in a comment). Never attribute a score to
GPT-4o-mini. Binary ASR threshold 0.5 unless stated.

---

## 2. The one-paragraph answer for this window

**The `d_surface` line is closed, and something else took its place.** Both Phase-1 gates failed:
Gate E7 (adding the axis suppresses ASR) turned out to be **a collapse in output length**, not in
compliance, and Gate DOSE showed the L12 removal effect is **entirely dose-driven** — at a dose inside
the in-subspace control band it is exactly zero, 0 net flips of 495. A first *positive* specificity
result (R-AG) was retracted 46 minutes later when its "matched" doses were re-measured in the space
the intervention actually acts in (6.60×, not 1.17×), and the repair arms returned the third and
first-clean specificity negative: **at genuinely matched dose the codeword and concept directions are
behaviourally indistinguishable, and both inert.** What replaced the axis is an intervention that fits
**no direction at all**, so no dose confound is possible: masking the generated answer's attention to
the demonstration block across a mid-stack band **suppresses the doublespeak attack** — Llama
0.2292 → 0.0521 (−0.1771) at L6–14 against an identically-key-matched late-layer control at 0.2083,
and Qwen3 0.1771 → 0.0104 (−0.1667) at the depth-matched L7–17. It is independent of the refusal
channel, scales with the number of demonstrations on both models, is redundant across layers (all 40
heads of L8 are dispensable), and has **no low-dimensional summary that tracks it** — attention mass
to the demonstrations *anti-predicts* causal importance on Qwen3, which kills the last candidate
objective. Establishing its *magnitude* then consumed thirteen hours and **seven downward corrections
of its own author's statistics**, ending at Phase 10: three demonstration pools, ten populations, two
models, k=18 clusters, **Δ = −0.0764 with a calibrated t-CI95 of [−0.1459, −0.0069]** — the first
cluster-level interval in the project that excludes zero, pre-registered at P = 0.941 before the data
landed. It remains carried by Qwen3 (p = 0.00195) with **Llama alone at p = 0.131**.

---

## 3. Scale and resources — exact census

All figures re-derived from git and the filesystem at HEAD `8c83c8f3`.

| quantity | value |
|---|---|
| commits since Part I's HEAD `016f3c98` | **113** (08-23: 31 · 08-24: 82) |
| commits inside the declared phase window 17:00 → 23:10 | **111** — two (`2ff8d24a` 16:38, `8bd07054` 16:51) sit in the 53-minute gap before the phase opened; `8bd07054` is the commit that created Part I |
| author identity | **113/113** `Omer Yosef <omeryosef@mail.tau.ac.il>`, author == committer, zero date skew |
| distinct SLURM job ids cited in the phase log | **104**, range **776368 – 779038** |
| status of the 40 most-cited (`sacct`) | 36 COMPLETED, **3 FAILED** (776437, 776656, 777122), **1 CANCELLED** (777530). Longest: 776797 `p1bjudge` 01:26:05 |
| run directories created under `outputs/boombness/` in the window | **204**, of which **199 carry `DONE.json`** — `judge` 100/100, `score_behavior` 58/57, `extract_boombness` 16/16, `tokenization_audit` 14/14, `crossbank_knockout_test` **9/6**, `retrieval_strength` 7/6 |
| `.md` deliverables touched | 6 files, 116 touches — **97× the phase log**, 6× `docs/BOOMBNESS_SPRINT_PROGRESS.md`, 6× `docs/BOOMBNESS_CONTINUATION_LOG.md`, 5× `reports/boombness_objective_sprint_report.md`, 1× each for Part I and the short update |
| `check_all.py` at HEAD | **exit 0 — all six guards pass** (`retraction_sweep`, `canonical_figures`, `verify_report_numbers`, `markdown_structure_check`, `pvalue_hygiene_check`, `plan_coverage_check`) |
| `tests/` at HEAD | 46 files, 643 top-level test functions; full run **721 passed, 18 failed, 7 skipped** in 145.55 s ⚠ see §11.3 |

**New prompt banks built and audited in this window — eleven, all at 2,736 rows / 336 2×2 families /
0 alignment violations / audits `2736 ok, 0 bad, 0 ambiguous`:**

`basket_bomb`, `basket_knife`, `button_knife` (08-23), `button_bomb` (the missing 4th cell of the
first crossing), `ticket_bomb`, `ticket_knife`, `window_bomb`, `window_knife` (codewords 3 and 4),
`basket_gun`, `button_gun` (concept 3), `basket_club`, `button_club` (concept 4).
**Rejected: `basket_arrow` / `button_arrow`** — see R-AZ (§7.7) — and deleted.

**Demonstration pools — five generated, four usable.** Each is produced by `src/boombness/demo_pools.py`
with the *same* generator, model and seed (`gpt-4o-mini`, `openai_seed 20260816`, `n_per_pool 40`,
24 pools, 6 domains × 4 valences). Content hashes: bomb `b5e399712b996b7d`, knife `5d3080f60af987c6`,
gun `79e93dbb2b65c820`, arrow `bb8bcc403f35b7f4` *(rejected)*, club `2fc70fe498d7c775`.
**Which pool a bank draws from is the independence axis that C-11 turned on** — see §6.8.

**The behavioural population, used by every arm in Phases 2, 3, 4, 8, 10** (R-B):

```
query_kind == "behavioral" AND condition == "natural_doublespeak"
AND bank_block in {core2x2, core2x2_slot3} AND n_examples in {1,2,4,8}
```

**n = 96**, one row per family (so family-disjoint *by construction*), 6 domains × 16, dev 48 /
heldout 48, 24 rows at each of `n_examples` ∈ {1,2,4,8}, 0 rows missing `demo_block`. Its ceiling is
**108 safe rows** — the bank cannot go higher without merging different design factors (§7.8).

**Compute.** GPU work was fair-share throttled for most of 08-24. Diagnosed rather than assumed:
all six L40S nodes read 8/8 allocated (`n-801…805`, `t-806`), `sshare` gives `FairShare 0.008446` on
`gpu-research`; widening `--nodelist` 5→6 was **tested with one submission before acting** and
changed nothing; `gpu-sharifm` is group-gated and `sbatch` rejects it; `studentkillable` has no L40S.
`cpu-killable` was unaffected, so all judging, pool generation and analysis ran at full speed.

---

## 4. The plan this window executed

Written at 17:20 on 08-23 as `external_md/BOOMBNESS_DSURFACE_NEXT_PHASE_PLAN_AND_PROGRESS.md`, with
the primary goal stated as **not** rescuing the old hypothesis but determining *what the surviving
mechanism actually is*, and whether this chain can be established cleanly:

```
demonstrations → retrieval / remapping mechanism → internal state / refusal interaction → harmful behaviour
```

| phase | question | gate | outcome |
|---|---|---|---|
| **0** | reproduce, audit, clean start | — | ✅ PASS |
| **1A** | does the exp-7 effect survive a real 3-draw control band? | **Gate E7** | ⛔ **FAILED** (R-F) |
| **1B** | does `d_surface` removal still move ASR at realized dose ≤ 0.13? | **Gate DOSE** | ⛔ **FAILED** (R-S) |
| **2** | is demonstration retrieval causally necessary for behavioural jailbreak? | **Gate RETRIEVAL** | ✅ passed on direction (R-R) |
| **3** | does retrieval act *through* refusal or beside it? | — | ✅ independent channels (R-T) |
| **4** | do Llama and Qwen3 share the mechanism? | headroom gate N13 | ✅ replicates (R-AA, R-AB) |
| **5** | build a bank whose cell means are **not** PC1-dominated | **bank acceptance** | ✅ PASSES (R-AC) |
| **6** | re-test concept generality on that bank | — | ✅ decomposition established; ⛔ specificity fails (R-AH) |
| **7** | only then, a new objective | 6 sub-gates | ⛔ **BLOCKED** — both candidate scalars closed |
| **8/9/10** | *(added in-flight)* power the causal claim by adding banks, then concepts, then pools | — | ⛔ **R-BD retracted by C-18**; and R-BE shows the added axis was the wrong one — see below |

Two standing rules governed everything and are worth carrying: **(a) never interpret a null without
first proving the intervention fired**, and **(b) write the reading of a result down before the result
exists.** Both are visible in the log as `📌 PRE-REGISTERED` blocks, and both fired: the pre-registered
falsifier in R-AO killed R-AN's reading, and the pre-registration in R-BB was scored against the real
Phase-10 outcome rather than re-derived after it.

---

## 5. Timeline

**08-23 16:38–17:20 — the handover.** Two commits close Part I (`8bd07054` writes it). At 17:09 a
commit lands that **neither of the two Claude sessions in contact claims** (`91e30a62`); the phase log
records the branch as having "an unreachable writer" and adopts a protocol: stage by explicit path,
never `git add -A`; `git log` before every commit. ⚠ Git cannot corroborate this — all 113 commits
carry an identical author *and* committer identity, so the third actor is invisible in the metadata
(§11.4).

**17:20–18:15 — Phase 0 passes, and Phase 2 turns out to be unrunnable.** OpenAI credits are verified
restored (HTTP 200 at 17:18), the queue is empty, `check_all` is 6/6. Then **R-A**: five independent
audits converge on two defects in `doublespeak_causality/pair_common.py`. `AttentionKnockout`
addresses query rows by **absolute prompt position**, so under KV-cached decoding the guard
`if qp >= am.shape[2]: continue` (line 469-471, verified verbatim) **skips every decode step** — the
block applies at prefill and switches itself off for the whole generation. A second guard,
`if 0 <= kp <= qp` (line 473), compares an absolute key index against a cache-local one. The existing
test **asserts this as intended** (`test_out_of_range_query_is_skipped_silently`, line 187) — correct
for the teacher-forced readout it was built for, fatal here. **The run would still have emitted rows,
still reported `n_edges_cut`, still exited 0, and produced a clean-looking, publishable, wrong null.**
Fixed additively as `AllQueryAttentionKnockout` (line 495) with `n_decode_forward` / `n_decode_edits`
liveness counters; the old class is left byte-untouched (the fix commit `24312889` has **zero deleted
lines**) because every committed G1/G3 artifact depends on its semantics. 10 tests ship with it,
including `test_old_class_is_dead_at_decode_THIS_IS_THE_REGRESSION_GUARD`.

**18:14–19:26 — both Phase-1 gates fail.** R-C (preliminary) then **R-S**: the L12 effect is
dose-driven. **R-F**: Gate E7's suppression is a length collapse. **R-G**: the "matched random
control" is a lottery spanning 0.325 in ASR. Decision D-8 promotes Phase 2 to the main line and
Phase 5 (the new bank) from "nicety" to "the fix for the thing that just broke".

**19:05 — REVIEW-1** (six adversarial reviewers, run *before* any GPU matrix) finds four must-fix
defects in the new Phase-2 code, the worst being **M4: the liveness gate, the span resolver and both
dose formulas had zero test coverage** — three reviewers independently mutated them and **44/44 tests
stayed green every time**, because `tests/test_realized_dose.py` re-typed the formulas instead of
importing the module. *The guard built to prevent dead guards was itself a dead guard.*

**19:34–21:02 — Phase 5's premise is measured, then built.** R-H shows on CPU, from three fits already
on disk, that crossing codewords against concepts drops PC1 from 0.78–0.95 to ~0.52 and the
arm/best-control dose gap from 6–12× to 2.1–2.7×. R-I builds three new banks (0 violations, 0
ungrammatical article usages in 16,416 rows — measured, not argued). **R-M**: at six pairs PC1 is
0.333–0.350 and the gap **1.35–1.62×**.

**20:32–20:56 — the instrument is declared void, then un-voided.** R-J reads the Phase-2 smoke against
its own pre-registered criteria and fails check 6 (generation barely changed) → **VOID**. R-L retracts
that 24 minutes later: length was a bad operationalisation, and the repo's existing
`generation_change.py` shows **8/8 = 100% of generations changed** at both depths. *"My own
pre-registration named the right alternative and I implemented only the weak half of it."*

**22:20 — REVIEW-2 catches a wrong headline before publication.** The Phase-2 text-deletion **ceiling
is one prompt**: `final_query_text` takes exactly 2 distinct values across all 1,152 behavioral rows,
so the 96-row `--demo-deleted` arm is **one prompt replicated 96 times, 1 distinct generation**. The
headline it would have produced — *"demonstration knockout recovers 100% of the deletion ceiling"* —
was already computable and already wrong. The review simultaneously finds where the real signal is:
the **arm-versus-matched-control contrast, which does not use the ceiling at all.**

**22:25 — PHASE 2 RESULT (R-R).** 0.2292 → 0.0521 at L6–14 against 0.2083 for the same keys cut at
L20–31.

**08-24 00:21 — PHASE 3 (R-T)**: retrieval and refusal are independent channels; the prediction
written before the arms landed held.

**00:41–01:52 — Phase 4 ports to Qwen3.** R-U proves the demo block is *addressable* under the Qwen3
tokenizer with no GPU; **R-V/C-3** kills the Qwen3 `d_surface` specificity claim in closed form (the
control removes **24.79× less**, and a dose-matched orthogonal control at L11 **cannot exist**);
REVIEW-3 fixes two real defects in the port and records the **S8 caveat before the numbers exist**;
R-AA clears the N13 headroom gate at 0.1875. **01:52 — R-AB**: the knockout replicates, and `C_all` is
degenerate on both models exactly as S8 predicted.

**02:21–03:24 — the geometry falls out in four hours, on CPU.** R-AC (bank gate passes) → **R-AD**
(`d_surface` = codeword ⊕ concept, orthogonal, equal) → **R-AE/C-4** (the *concept* axis `N` is real
and invariant; the *codeword* "axis" is a subspace) → **R-AF/C-5** (all four K=4 predictions confirmed;
one of my own arguments was near-circular) → Phase 6d, the first genuinely dose-matched specificity
test the project can run.

**04:00–05:00 — the sprint's fastest retraction.** **R-AG** publishes the first positive specificity
result at 04:00. **C-6** retracts its headline at 04:35 — the dose was measured against *centred* cell
means while the hook subtracts from the **un-centred residual**; the real ratio is **6.60×**, not
1.17×. **R-AH** at 05:00 settles it with repair arms: at a real dose *below* the inert concept arm, the
codeword arm does nothing. **Third specificity negative, first clean one.**

**05:02–08:53 — Phase 7 closes on evidence.** R-AI (the retrieval account makes a prediction the dose
account cannot, and it holds on both models) → R-AJ (measurement gate passes, **prediction gate fails**
— the scalar is `n_examples` wearing a different name) → R-AK (**attention mass anti-predicts causal
importance on Qwen3**) → R-AL/C-8 (that generalisation was an averaging artifact; at head granularity
the causal band wins) → R-AM (**all 40 heads of L8 are dispensable**) → R-AN → R-AO/C-9 → R-AP →
**R-AQ/C-10**: three successive layer "laws" retracted, because they were fitted to **1–3 prompt
differences smaller than the measurement's own session-to-session reproducibility.** Decision D-12:
stop subdividing the band.

**08:53–19:23 — the statistics war.** Phase 8 replicates across banks (R-AR, p = 2.44e-04) → **C-11**
(the four banks share only **two** demonstration pools; p → 1.56e-02) → REVIEW-5/C-12 → R-AS →
R-AT/R-AU (a Llama null that is really 6 removed + 7 created) → R-AV/C-13 → R-AW → **C-14/REVIEW-6**
(both retracted: the percentile bootstrap is ~30% too narrow at small k) → **C-15** (`model` is not an
independent axis; the defensible interval includes zero **by 0.0029**) → R-BA → **C-16** (self-found
one hour later: the p is sign-only) → **C-17/REVIEW-7** (withdrawn entirely; it fails
leave-one-**model**-out). At 19:51 a **LIVE CLAIMS LEDGER** is added to the top of the log because
*"after 17 corrections the log is dangerous to read."*

**20:11–23:05 — Phase 10.** R-BB computes what would settle it — **one more demonstration pool** —
finds the corpus already exists, queues it, and pre-registers the outcome; R-BB-refined simulates it
(P = 0.92–0.999 under every branch); the interim flags that the gun pool looks like the *pessimistic*
branch and **declines to compute the favourable-looking subset early**; R-BB-refined-again carries a
measurement-depth penalty and registers **P = 0.941**. **23:05 — R-BD: k=18, the calibrated CI excludes
zero.** In the same result, a **silent-overwrite bug in the author's own tool** is caught by
cross-checking it against a hand computation.

---

## 6. WHERE WE WON

Every number below was re-derived from the named artifact.

### 6.1 The headline: demonstration-retrieval knockout suppresses the doublespeak attack

The intervention is `demo_all:attn_knockout:<band>:1.0` — during generation, every query row is
blocked from attending to the demonstration-block key positions across a band of layers. It **fits no
direction**, so the dose confound that governs all of Part I **cannot apply**. Every arm was verified
live before being read (`frac_rows_decode_live = 1.0`, gate refuses < 0.99).

**Llama-3.1-8B, L6–14** (R-R, judge session 776893, `n_common = 96`):

| arm | ASR@0.5 | Δ vs baseline | refused | median chars | distinct completion lengths |
|---|---|---|---|---|---|
| **A** baseline | **0.2292** | — | 0.031 | 788 | 84/96 |
| **C_band** L6–14 | **0.0521** | **−0.1771** | **0.010** | 771 | 77/96 |
| **D_ctrl** L20–31 *(identical key set)* | **0.2083** | −0.0208 | 0.042 | 793 | 84/96 |

**Arm minus control: −0.1562.** Per-domain, exact paired cluster sign-flip on `C_band` vs `D_ctrl`:
5 of 6 domains negative, none positive, **p = 2/32 = 0.0625 — exactly the attainable floor** for 5
informative clusters, so the magnitude is the quotable quantity, not the p.

**Checked rather than assumed:** it is **not degeneracy** (77/96 distinct completion lengths vs the
baseline's 84; contrast `C_all` at 24), **not a refusal effect** (refusal *falls*, 0.031 → 0.010), and
**not truncation** (median 788 → 771, against the `d_surface:add` collapse of 67 → 25 in R-F).

⚠ **What the completions contain is uncharacterised.** `goal_topicality` reads 0.0000 on the baseline
too (`frac_zero` 0.990) — expected by construction, since a *successful* doublespeak attack complies
while still speaking in the codeword, so the goal's distinctive word never appears. The mechanism
gloss *"the model loses the carrot→bomb mapping and answers the literal question"* is a **hypothesis,
not a finding**, and this bank has no instrument that can test it.

### 6.2 Retrieval and refusal are independent channels (R-T)

Judge session **777030**, all four 2×2 cells judged together, `n_common = 96`:

| cell | ASR@0.5 | refused | Δ vs A |
|---|---|---|---|
| **A** baseline | 0.2292 | 0.0312 | — |
| **C** retrieval knockout L6–14 | 0.0521 | 0.0104 | **−0.1771** |
| **R** refusal removed (`refusalness:project_out:12-12`) | 0.1979 | 0.0417 | −0.0312 |
| **C+R** both | **0.0208** | 0.0208 | −0.2083 |

**The knockout's effect is the same size with refusal intact (A→C, −0.1771) and with refusal removed
(R→C+R, −0.1771)** — a net of exactly −17/96 in both. Against the pre-registration written before the
arms landed (`C+R ≈ C` ⇒ independence, `C+R ≈ R` ⇒ mediation): `|C+R − C| = 0.0312` versus
`|C+R − R| = 0.1771`. **Independence confirmed.** Removing refusal *alone* does almost nothing on this
bank (−0.0312), which is not a contradiction of Part I's large refusal channel — that was measured on
AdvBench, a different population.

⚠ **Correction found by this audit (§11.1, defect 3):** the log's gloss that the knockout "removes the
same ~17 prompts regardless of refusal state" is not supported. The **nets** are −17 in both, but
**23 prompts cross the threshold in A→C (20 down, 3 up) and 19 in R→C+R (18 down, 1 up)**, and the two
down-sets overlap in only **7** prompts. The additivity conclusion, which rests on the ASR deltas,
stands; the per-prompt identity does not.

### 6.3 It replicates across models (R-AA, R-AB)

The headroom gate first: Qwen3 complies with only **4/495 = 0.008** of AdvBench, and an intervention
cannot be measured against a floor (Part I's N13). On *this* bank Qwen3's baseline is **0.1875**
(judge 777118, 96/96 rows) — 23× that floor and within 4.2 points of Llama — with a graded score
distribution (`0.0 ×69, 0.12 ×1, 0.25 ×3, 0.38 ×5, 0.5 ×6, 0.75 ×3, 0.88 ×3, 1.0 ×6`), so the ASR is a
real rate and not an artifact of the cut point.

| | **Llama-3.1-8B** (32 blocks) | **Qwen3-14B** (40 blocks) |
|---|---|---|
| baseline **A** | 0.2292 | **0.1771** |
| **C_band** | **0.0521** (L6–14) | **0.0104** (L7–17) |
| **Δ band** | **−0.1771** | **−0.1667** |
| **% of baseline removed** | **77.3%** | **94.1%** |
| **D_ctrl** | 0.2083 (L20–31) | 0.1146 (L25–39) |
| Δ control | −0.0208 | −0.0625 |
| `C_all` | 0.0000 (L0–31) | 0.0000 (L0–39) |

The bands are **depth-matched, not count-matched** (0.19–0.44 of depth on both), and that asymmetry
was recorded before the numbers: a wider band can only make the knockout stronger, so it is
conservative for a positive result. **Qwen3's population is cell-for-cell identical to Llama's**, so
this is matched prompts, not merely matched counts.

⛔ **`C_all` must not be read as 100% suppression on either model.** It is degenerate: 96 generations
collapse to **24 distinct strings on Llama and 10 on Qwen3**. This was pre-registered as caveat **S8**
in REVIEW-3 *before the numbers existed* — because `lo = max(0, kp − past)` blocks each demonstration
token from attending to itself and to earlier demonstration tokens, so the all-layers arm destroys the
demonstrations' own computation rather than blocking retrieval of it. **The band arm, not the
all-layers arm, is what supports the retrieval reading.** It also retroactively qualifies Part I's G3
prior that all-layers was "the arm with a prior" — that prior was partly reading degeneracy.

⚠ **Where Qwen3 is weaker, stated plainly:** the arm-vs-control contrast gives
`C_band − D_ctrl = −0.1042, p = 0.5000` with only **2 informative domains** (floor 0.5000), because
`C_band` drives ASR to exactly 0.0000 in five of six domains and leaves no variance to test on. And
Qwen3's late-layer control is **not inert** — it removes 35% of Qwen3's baseline against Llama's 9%,
so depth specificity is **sharper on Llama**, the opposite of the headline direction.

### 6.4 The identification problem is solved by a crossed bank (R-H → R-M → R-W → R-AC)

This is the fix Part I prescribed, delivered and measured. The quantity that matters is not "does PC1
dominate" but **what dose the best possible orthogonal direction can attain** — that is the ceiling on
any specificity claim.

| design | rank | arm dose | best orthogonal | **arm/best** |
|---|---|---|---|---|
| single pair, Llama L12 *(every Part-I result)* | 3 | 0.8204 | 0.1202 | **6.83×** |
| single pair, Qwen3 L11 | 3 | 0.8997 | 0.0640 | **14.05×** |
| new single-pair banks (`basket_bomb` / `basket_knife` / `button_knife` / `button_bomb`) | 3 | 0.76–0.89 | — | **4.20× – 11.12×** |
| **12-cell crossed (3 banks)** | **9** | 0.3225 | 0.3170 | **1.02×** (L10) |
| **16-cell crossed (4 banks)** | **12** | 0.3108 | 0.2772 | **1.03–1.12×** |

**Every new single-pair bank fails, and the reason is structural, not lexical:** 4 cells → rank 3
after centring; in a rank-3 span with one axis carrying 76–89%, the orthogonal complement is small
*by construction*. Changing `bomb`→`knife` or `carrot`→`basket` changes which words are involved; it
cannot change the rank. **The fourth cell `button_bomb` was built and measured *after* that prediction
was written, and failed the same way (4.34/4.81/5.29× at L10/12/14).**

**Gate verdict (R-AC), against the plan's three stated criteria:** PC1 does not dominate
(**0.3607** at L12 over 16 cells, vs 0.76–0.89 on every single-pair bank) ✅; comparable attainable
doses (**1.03–1.12×**, robust across arm choices at 0.63–1.20×) ✅; tokenization/alignment/grammar
audits pass ✅. **For the first time in the project, "same dose, different direction" is testable.**

⚠ The cells still come from four *independently fitted* banks, so the 0.2783 "bank/pair identity"
component contains between-bank nuisance. A single jointly-generated crossed bank remains the stronger
version and was not built.

### 6.5 `d_surface` decomposes into codeword ⊕ concept (R-AD, R-AE/C-4, R-AF/C-5, C-7)

All CPU, from fit payloads already on disk. **Split-half ceiling first**, so nothing below can be
dismissed as noise: `cos(dev, heldout)` for the same direction fitted on disjoint halves is
**0.9873 / 0.9879 / 0.9908** at L10/L12/L14 (mean over four pairs). These directions are measured
almost noiselessly.

**Cross-pair cosines at L12, as a fraction of that ceiling:**

| relationship | fraction of ceiling |
|---|---|
| same **CODEWORD**, different concept | **0.5373** |
| same **CONCEPT**, different codeword | **0.5177** |
| **differ in both** | **0.0599** |

Sharing either factor gives ≈ ½; sharing neither gives ≈ 0 — the exact signature of `d = (W+N)/√2`
with `W ⟂ N`. Fitting the model directly confirms it at **every layer 12–31**: `cos(W,N)` never leaves
[−0.035, −0.004], `‖W‖ ≈ ‖N‖ ≈ 0.50`, and the interaction never exceeds 0.065.

**The log is careful about what is by construction and what is not.** A saturated 2×2 has 4 cells and
4 degrees of freedom, so the residual *being* the interaction and `cos(d, rec)` being high are
automatic and are **not** evidence. What does not follow from anything: the **orthogonality**, the
**equal magnitudes**, the **small and depth-shrinking interaction**, and the fact that the cross-pair
cosines reproduce the additive prediction **without fitting W or N at all**.

**Then the naming was corrected twice, by its own author's pre-registered falsifiers:**

* **C-4** — with a *third* codeword, the codeword-mean matrix has **rank 2** with two comparable
  components (0.617/0.383 at L12). `W` was never a factor axis; it was the `basket−button` **chord of
  a 2-simplex**. In general the codeword factor is a **(K−1)-dimensional subspace**.
* **C-5** — for K centred equal-norm vectors the mean pairwise cosine is **forced** to −1/(K−1), so
  "converging on −0.5" was arithmetic, not evidence. What survives is the *spread* (sd collapsing
  0.109 → 0.032 with depth) and the *norm equality* (CV 0.111 → 0.021), neither of which is forced.
* **C-7** — an adversarial review showed three of four "pre-registered predictions" were satisfied by
  **chance geometry in ℝ⁴⁰⁹⁶**: an isotropic null of four random unit vectors gives singular² fractions
  0.3419/0.3331/0.3244, norm CV 0.0066 and cosine sd 0.0123 — **more regular than the data**. The
  "near-regular simplex" framing is withdrawn. *Recorded lesson: "a prediction is only a test if a null
  model can fail it — and I did not run a null model until an adversarial review made me. Every future
  geometric claim in this phase gets an isotropic null first."* **That rule was then actually followed**
  (R-AX and R-BC both compute their null before the data exists).

**What survives all three corrections, and is the strongest single claim of the window:**

> **The concept axis `N` (the bomb−knife contrast) is invariant to which codeword estimates it, at the
> split-half ceiling.** Six pairwise cosines at L14: **0.987, 0.988, 0.984, 0.986, 0.989, 0.984**
> against an isotropic null (1,200 draws) whose median is **−0.0007** and whose **|max| is 0.0569**.
> `N` estimated from `{window}` alone — a codeword that did not exist when `N` was named — matches `N`
> from the other three at **0.9790 / 0.9897 / 0.9937**, i.e. **99.2% / 100.0% / 99.96% of ceiling**.

Variance accounting over the six K=3 banks: the concept axis (1 df) carries **0.4290–0.4440** of the
between-bank spread and the codeword subspace (2 df) **0.5529–0.5714** *(the log says 0.5722; see
§11.1 defect 1)* — so **per dimension the concept axis is roughly twice as strong as any codeword
dimension.** R-AD's "equal magnitude" was an artifact of the codeword side having two degrees of
freedom.

### 6.6 Concept identity is a plane, not an axis (R-AX, R-AY, R-BC)

With `gun` as a **third concept** (the one expensive step, run only after explicit user go-ahead) and
`club` as a **fourth**, the same falsifier that demoted `W` was applied to `N` — and it fired.

**Three concepts, codeword fixed at `basket`** (R-AX): PC1 of the centred concept directions is
**0.7132 / 0.6979 / 0.6275 / 0.6070** at L12/14/18/24. One axis would require PC1 = 1.0, so
**concept identity is not one axis**; but the isotropic null for three centred unit vectors is
**0.5075, 95% [0.5015, 0.5173]**, so the concepts are also **substantially more collinear than
chance**. `gun` sits *between* `bomb` and `knife` (cos 0.7509 and 0.7225 against their mutual 0.5245).
**Replicated on `button`** (PC1 0.6657/0.6020/0.6004), with each concept contrast reproducing across
codewords at **0.9638 / 0.9671 / 0.9720** — the concept subspace is codeword-invariant.

⚠ The null also contained a trap the log records: `cos(bomb−knife, bomb−gun) = +0.6495` looks like
strong alignment, but the null for *any three vectors whatsoever* is **+0.4999**, because the two
contrasts share a term. Nearly all of it is the shared term.

**Four concepts** (R-BC), with the null fixed **before `club` — indeed before `arrow` — existed**:
PC3 under isotropy is **0.3246, 95% [0.3170, 0.3297]**. Observed PC3 is **0.1640 / 0.2254 / 0.2438**
(basket) and **0.1874 / 0.2429 / 0.2492** (button) at L12/18/24 — **below the null's lower bound at
every layer on both codewords, and far above zero.** Neither of the two extreme pre-registered
branches fired; **the intermediate one, written down in advance, did**: a **dominant plane**
(PC1+PC2 = 0.836 at L12) with **real but suppressed third-direction structure that grows with depth**.

The semantic arrangement is coherent and was not put in by hand: at L12, `bomb~gun` 0.7509 >
`knife~gun` 0.7225 > `gun~club` 0.6277 > `knife~club` 0.5649 > `bomb~knife` 0.5245 > `bomb~club`
0.4936. **Explosive and blunt instrument are the extremes; a firearm sits between them and the blade.**

### 6.7 The mechanism is layer-redundant, and has no low-dimensional handle (R-AM, R-AQ/C-10)

| arm (Qwen3, judge 777331, one session, n=96) | ASR | Δ | % of band effect |
|---|---|---|---|
| `A_baseline` | 0.1667 | — | — |
| **band L7–17, ALL heads** | **0.0000** | **−0.1667** | 100% |
| **L8, ALL 40 heads** | 0.1771 | **+0.0104** | **−6.3%** |
| L8 head 22 only *(top demo-attention head in 72/96 prompts)* | 0.1458 | −0.0208 | 12.5% |
| L8 head 30 only *(seeded control)* | 0.1667 | +0.0000 | 0.0% |

**Cutting demonstration attention at an entire layer — all 40 heads — moves ASR by one prompt of 96,
in the wrong direction, while the same cut across the 11-layer band removes the attack completely.**
The layer-level ceiling is what makes the head result interpretable, and it says the head question was
**ill-posed at that layer**. Combined with R-AK (below): **where the model looks is not where the work
happens.**

**What survives the three retracted layer laws (C-10):** ≥8 contiguous layers produce a large effect
(`L10–17` −0.1250/−0.1771/−0.1771 and `L7–17` −0.1562/−0.1354/−0.1979 across three sessions); any
window of ≤6 layers produces a small one (eight measurements, all in −0.01…−0.09); **position within
the band is not resolvable**, and **the lower band is not inert** (`L7–9` alone = −0.0625, identical to
`L10–12`). **D-12: the band-localisation question is closed as unresolvable at n = 96 with 6 domain
clusters.**

### 6.8 ⛔ RETRACTED BY C-18 — the Phase-10 calibrated result (R-BD)

> **This whole subsection is superseded.** See the POST-PUBLICATION CORRECTION at the top: the k=18
> `pool × domain` unit is a crossed 3×6 table on one shared 96-prompt set, both of whose marginals
> include zero. The numbers below are reproduced exactly as the artifact stores them and are correct
> *as arithmetic*; what fails is the **unit**, and therefore the claim built on it. Read it as the
> record of a retracted result, not as a live one.

The magnitude claim took **five clustering units, four statistics and seven corrections** to state
defensibly. The design axis that matters is the **demonstration pool**, because C-11 discovered that
"four independent banks" were really **two pools**: `main` and `ticket_bomb` share
`b5e399712b996b7d`; `button_knife` and `window_knife` share `5d3080f60af987c6`; and **all 96
`prompt_id`s are identical across all four banks.** Phase 10 added a **third** pool (`gun`) purely to
buy cluster count — and its outcome was pre-registered at **P = 0.941** before the Llama arm landed.

**Artifact:** `outputs/boombness/crossbank_knockout_test/xb10final_20260824_230323_1997748/crossbank_test.json`
— **10 populations (5 banks × 2 models), 3 pools, 2 models**, 96 rows each, every knockout arm
verified live first.

| statistic (threshold 0.5) | value |
|---|---|
| **`pool × domain`, k = 18, mean Δ** | **−0.0763888888888889** |
| **calibrated t-CI95** | **[−0.14585082748301995, −0.006926950294757844]** — **excludes zero** |
| `pool × domain` exact sign-flip p | **0.0068359375** |
| `cluster_permutation_on_counts` | **T = −83, p = 0.00390625**, `p_is_sign_only = **False**`, 12 informative of 15 |
| worst **group** drop | **0.0625** (dropping the bomb pool) |
| per model | **Qwen3 p = 0.001953125** · **Llama p = 0.130859375** |
| prompt-level exact binomial | **113 down / 30 up**, p = **1.5773e-12** |
| both-arms-EOS control | **30 / 1**, p = **2.9802e-08** |

**Two things make this the first defensible magnitude statement in the project.** First,
`p_is_sign_only = False`: with a positive gun cluster present, `|T|` is no longer maximal, so the
magnitudes actually enter the p-value — which is exactly the defect C-16 caught in R-BA. Second, the
mean **fell** as predicted (−0.1016 → −0.0764, because the gun pool is weak) and the CI still excluded
zero, **because six more clusters cut the standard error faster than the weaker pool diluted the mean**
— the arithmetic R-BB identified in advance.

⚠ **Stated at its real strength:** Llama alone is p = 0.131, the worst group drop is 0.0625, and the
upper CI bound is 0.0069 below zero **on a scale where one prompt flip in one 16-prompt cell is
0.0625**. The exclusion is real and thin. **The claim is "excludes zero at the defensible clustering",
not "robust to dropping either model."** The log says this itself.

### 6.9 The process layer

Every guard in this window shipped with a test that **fails the pre-fix code**, and several were
verified by **mutation** rather than inspection:

| guard | what it prevents | mutation evidence |
|---|---|---|
| `AllQueryAttentionKnockout` liveness (`frac_rows_decode_live`, gate 0.99) | a knockout that switches off during decoding | 27 tests pass CPU-only in 25.8 s; the regression guard asserts the *old* class's failure |
| `tests/test_knockout_liveness_gate.py` (17 tests) | the four REVIEW-1 defects | mutating the gate to `< 0.0` → 3 red; span `+1` → 2 red; dose → `frac*alpha` → 2 red; control ignoring the protected span → 2 red (the old 44-test suite stayed **green on all four**) |
| `tests/test_band_range_and_abort.py` (9) | a band silently under-covering a deeper model | removing the band check → 4 red; removing the abort marker → 2 red |
| `tests/test_knockout_heads.py` (7) | a "head 22" arm that silently blocks all 40 | `test_default_is_still_all_heads` pins `heads=None` for every Phase 2–4 arm |
| `tests/test_crossbank_stratification.py` (18 now, 7 at creation) | a stratification that never stratifies | reinstating `A[p].get("truncated")` turns it red |
| `scripts/install_commit_guard.sh` + `tests/test_commit_guard.py` (6) | committing on a red `check_all` | planted a retracted figure → guard red → commit **refused**; the hook uses `set -uo pipefail`, **not `set -e`**, because with `set -e` the `OUT=$(...)` capture aborts before `RC` is read and a red check would exit 0 through the hook |

The last one exists because of a genuine failure at 14:51: *"I ran `check_all.py`, it printed
`1 of 6 guards FAILED: retraction_sweep`, and I committed anyway"* — the shell lines were
newline-separated rather than `&&`-chained. The bad commit `fba11847` stands in history; the tree was
repaired 113 seconds later in `63f46f22`. ⚠ **Coverage limit this audit found and the log does not
state:** `.git/hooks/pre-commit` has mtime 2026-08-24 15:23:33, i.e. **95 of the 113 commits predate
the hook file entirely**, and the "process fix" commit that installs it (`94e26204`, 15:22:11) is
itself **82 seconds older than its own hook**. The protection covers roughly the last 18 commits.

---

## 7. WHERE WE FAILED

### 7.1 Gate E7 FAILS — the suppression was a length collapse (R-F, R-G)

`d_surface:add` at 0.5 gap on AdvBench-495 gives ASR 0.004040 against a baseline 0.064646 — but:

| arm | median chars | mean chars | frac < 80 ch | `scorable_frac` |
|---|---|---|---|---|
| baseline | 67 | 242.2 | 0.786 | 0.5414 |
| **`dS50`** | **25** | **68.0** | **0.939** | **0.1172** |

Conditioning on both arms' completions being ≥ T characters, paired on `prompt_id`:

| T | rows kept | baseline ASR | arm ASR | Δ |
|---|---|---|---|---|
| 0 | 495 | 0.064646 | 0.004040 | −0.060606 |
| 40 | 51 | 0.137255 | 0.039216 | −0.098039 |
| **80** | **22** | **0.090909** | **0.090909** | **+0.000000** |
| 120 / 200 / 400 | 21 / 19 / 15 | — | — | **+0.000000** each |

**Exactly zero at every threshold from 80 characters up.** Of the **32** baseline successes, **30**
have an arm completion under 80 characters — the judge was scoring near-empty text. And the control
band is a **lottery**: four same-dose random draws span **−0.2188 to +0.1064** on length-matched rows,
against a published arm effect of 0.036; `r02` alone drives refusal to **0.986** and ASR down 0.22
*while still writing 148-character answers*. **A single-draw "matched random control" at this
magnitude is uninterpretable.**

⚠ The log states the collider caveat itself: conditioning on completion length conditions on a
**post-treatment variable**, and asymmetrically (`dS50` retains 22 rows, the random arms 77–96). What
the table establishes is not "the effect is an artifact" but **what the effect is made of** — and
*"adding `d_surface` truncates generation"* is a very different claim from *"it suppresses jailbreak
behaviour"*, and not one anybody would optimise. **This supersedes the follow-up line's
"EXPERIMENT 7 ANSWERED" headline.**

### 7.2 Gate DOSE FAILS — the L12 effect is dose, not direction (R-C, R-S)

Fourteen arms judged in **one session** against one baseline, AdvBench-495, `n_common = 495`
(`outputs/boombness_followup/gate_dose_ladder.json`, job 776797):

| α | realized variance dose | Δ ASR (clustered) | p_cl |
|---|---|---|---|
| **1.00** | 0.8204 | **+0.0319** | **0.0054** ✅ |
| 0.38 | 0.5051 | +0.0086 | 0.0961 |
| 0.30 | 0.4184 | +0.0071 | 0.1474 |
| 0.20 / 0.15 / 0.10 | 0.2954 / 0.2277 / 0.1559 | +0.0045 / +0.0052 / +0.0039 | 0.2575 / 0.1899 / 0.2806 |
| 0.08 / 0.06 / 0.056 | 0.1260 / 0.0955 / 0.0893 | +0.0025 / +0.0039 / +0.0030 | 0.4974 / 0.2728 / 0.4300 |
| 0.045 / 0.03 | 0.0722 / 0.0485 | +0.0039 / +0.0021 | 0.2806 / 0.5910 |
| `ctrlrnd` (random, full dose) | — | −0.0018 | 0.3504 |
| **`ctrlort`** (in-subspace ⊥, **full** dose) | — | **+0.0102** | 0.0640 |

**Only α = 1.0 is significant.** Refusal is flat at 0.9313 — identical to baseline — for every arm at
α ≤ 0.10: these arms do not merely fail to raise ASR, **they do nothing at all**. And the sharpest
single line against specificity: **`ctrlort`, a direction *orthogonal* to `d_surface` at full dose,
beats `d_surface` itself at every reduced dose.** *Dose beats direction identity.*

This also closed a worry the log had raised itself (**C-2**): variance-matched and norm-matched
definitions of "dose" disagree by roughly an order of magnitude in α about *which* arm is matched.
Both were pre-registered and reported. **They disagreed about which arm was matched and agreed
completely about the answer.**

### 7.3 The fastest retraction in the project: R-AG → C-6 → R-AH

**R-AG (04:00)** was the first positive specificity result the project had ever produced: two
orthogonal directions (`cos = +0.0098`) on the crossed bank, apparently matched to 1.17× in dose,
producing effects differing by 26× — `W_codeword` +0.2708, `N_concept` +0.0104.

**C-6 (04:35) retracted its headline.** `cellmean_dose` measures a direction against the **centred**
cell means; the hook `AllPositionProjectOut` subtracts from the **actual un-centred residual** at every
position and every decode step. The two differ by the grand mean, **and the grand mean is where the
asymmetry lived** (`cos(grand_mean, W) = 0.3885` vs `cos(grand_mean, N) = 0.1402`). On the cell the
arms actually ran on:

| arm | fraction of ‖m_C‖ actually removed |
|---|---|
| `N_concept_axis` | **8.31%** |
| `W_codeword_pc1` | **54.84%** |

**The real ratio is 6.60×, not 1.17×.** *"The W arm deletes over half the residual at every token.
'Ablating 55% of the residual makes the model comply more' is a dose statement, not an identity
statement."* The same section notes this is the fourth appearance of the identical failure (6.83×,
24.79×, 14.05×, now 6.60×) and that **this one was worse, because it was dressed as the fix.**

**R-AH (05:00) settled it with repair arms run at a dose *below* the inert concept arm:**

| `basket_bomb` (judge 777289) | real dose | ASR | Δ vs A | cluster p |
|---|---|---|---|---|
| `A_baseline` | — | 0.2812 | — | — |
| `N_concept_axis` @1.00 | 0.0831 | 0.2708 | −0.0104 | 1.0000 |
| **`W_codeword` @0.12** | **0.0658** | 0.2917 | **+0.0104** | **1.0000** |
| `W_codeword` @1.00 | 0.5484 | 0.5729 | +0.2917 | 0.0625 |

Ordering the three interventions by real dose — 0.0658, 0.0831, 0.5484 — the effects are +0.0104,
−0.0104, +0.2917. **Effect tracks dose; it does not track identity.** On a second bank
(`button_knife`, judge 777290) R-AG does not replicate at all: every arm within ±0.021 of baseline,
including one that removes **41% of the residual at every token**.

> **The honest summary of the whole `d_surface` line: it is a real, reproducible, well-characterised
> representational object with no demonstrated causal role in the behaviour.** That is the same
> representation ≠ behaviour dissociation the earlier sprint recorded, now established with a bank
> built specifically to give identity a chance.

### 7.4 Both Phase-7 objective candidates are closed on evidence

| Phase 7 gate | `d_surface` | retrieval-strength (attention mass) |
|---|---|---|
| measurement | ✅ | ✅ instrument sane, monotone in demo count on both models |
| prediction | — | ⛔ **R-AJ** — vanishes within `n_examples` strata (3 of 4 exactly 0.0000) |
| causality | ⛔ R-AH | ✅ the *knockout* is causal and cross-model |
| specificity | ⛔ **R-AH** | ✅ layer-specific on both models |
| transfer | — | ⛔ **R-AK** — its relation to causality **reverses** across models |
| optimization direction | ⛔ | ⛔ would ascend the wrong band on Qwen3 |

**R-AJ:** the scalar is real — `demo_mass(band) = 0.06295` vs `late 0.03864`, band > late in **88 of
96 rows**, perfectly monotone in `n_examples` (+0.00571 / +0.01688 / +0.03028 / +0.04439). Its median
split looks decisive (HIGH −0.2917 vs LOW −0.0625). **It does not survive conditioning on
`n_examples`**: within-stratum baseline high−low is **0.0000 / 0.0000 / +0.1667 / 0.0000**. The
median-split result is `n_examples` wearing a different name.

**R-AK:** on Qwen3 the causal band **attends less** to the demonstrations than the inert control band
(0.03163 vs 0.04158; band > late in **6 of 96 rows**), yet its knockout is the one that destroys the
attack. On Llama the two agreed (91.7% of rows) — **so the agreement on Llama was a coincidence of that
model, not a property of the mechanism. One model was never enough to notice.**

**R-AL/C-8 narrowed R-AK honestly:** at *head* granularity the causal band's top head does exceed the
late band's on Qwen3 in 71/96 rows (p = 2.87e-06), so "not causally relevant at **any** granularity"
was withdrawn. The reason no single statistic works on both models is architectural: **Qwen3 routes
demonstration attention through one head (L8 h22, top in 72/96 = 75% of prompts); Llama spreads it over
at least four, none above 28%.** A mean detects the distributed case; a max detects the concentrated
one. Then R-AM showed L8 h22 is **causally inert** anyway.

> **What survives is the intervention, not any scalar.** Every attempt to reduce the mechanism to a
> number that could be optimized has failed. **"Ascend the retrieval signal" has no target to ascend.**

### 7.5 Three layer "laws", retracted in five hours (R-AN → R-AO/C-9 → R-AP → R-AQ/C-10)

R-AN concluded super-additivity; R-AO withdrew "needs the whole band" and substituted localisation to
L10–17; R-AP fitted a quantitative law (effect per effective layer rising 5.3 → 7.4 → 9.5 → 11.2).
**R-AQ retracted all of it in one within-session test:** `L7–9` gives **−0.0625, identical to
`L10–12`**, so the law's own prediction that L7–9 contributes zero **failed outright**; and `L7–12`
(6 layers) gives −0.0417, *less* than either 3-layer window inside it.

The diagnosis is the important part, and it generalises:

| arm | s777340 | s777351 | s777363 | s777372 |
|---|---|---|---|---|
| L7–9 | −0.0208 | — | — | **−0.0625** |
| L10–12 | — | — | −0.0312 | **−0.0625** |
| L7–12 | −0.0104 | −0.0104 | — | **−0.0417** |

**The same arm re-measured moves by 2–3 prompts.** Every sub-8-layer arm sits inside a −0.01…−0.09
band that its own session-to-session spread cannot resolve. *"R-AN, R-AO and R-AP each fitted a
different structure to differences smaller than the measurement's own reproducibility. That is the
error, and it is mine three times over."*

### 7.6 Seven downward corrections of one headline (R-AR → C-17)

This is the window's defining failure mode and it is worth tabulating, because the *effect* survived
all seven and only its *characterisation* kept being wrong.

| # | claim as published | why it fell |
|---|---|---|
| R-AR | `p = 2.44e-04`, 24 bank×domain clusters | **C-11**: the four banks share only **two demonstration pools**; all 96 prompt_ids are identical. Corrected to **p = 1.56e-02** |
| REVIEW-5 | (confirms C-11 independently) | + four more defects: `main` is the discovery sample reused; the sign test is sign-only (two informative clusters rest on **1 prompt** each); p is exactly `2/2^k`, 64× threshold-sensitive; **no persisted artifact** |
| R-AV/C-13 | "the cluster p is an artifact; the bootstrap CI excludes zero at **every** unit" | **C-14**: the percentile bootstrap has no small-sample correction — measured false-positive rate **6.4% at k=24, 8.6% at k=12, 14.2% at k=6, 18.6% at k=4**. Calibrated, k=6 and k=4 **include** zero |
| R-AW | "every knockout arm excludes zero, every control includes it" | **C-14**: the tail counts are the arithmetic floor `(n_zero/k)^k`. *"They would read identically if the effect were −0.001"* |
| C-13 | "after removing domain the banks are anti-correlated" | **C-14**: centring 4 profiles forces `r = −1/3`; simulated under pure independence **−0.3044** vs observed **−0.3102**. And its own two positive residual correlations were exactly the **same-pool** pairs — *"a confirmation of the pool dependence, read as a refutation"* |
| R-AY | "the pre-registered unit excludes zero" | **C-15**: `model` is not an independent axis — `corr(Llama, Qwen3)` after removing the domain main effect is **+0.5654** against a null upper bound of **+0.3153**. At the defensible unit the CI is **[−0.2060, +0.0029]** — fails by **0.0029**, reported as failing rather than rounded into success |
| R-BA | "weights by evidence AND respects clustering, p = 0.0156, robust to any single drop" | **C-16** (self-found, one hour later): shrinking every cluster net to ±1 gives the **identical p** — it is a sign test. **C-17**: it fails leave-one-**model**-out (Llama p = 0.1094); removing 10% of the evidence (the knife pool) takes p to 0.1250; and `cluster_permutation_on_counts` **was never called from `main()`** — *"I persisted the code and not the result, and the code was not even reachable"* |

Two details are worth keeping. **C-16 was self-found**, and the check that catches it is cheap and is
now run by default: *destroy the magnitudes, keep the signs, and see whether the p moves.* And when
REVIEW-7 offered a friendlier replacement statistic (cluster bootstrap on the nets, "CI excludes 0"),
the log **recomputed it under calibration, found it also fails ([−17.464, +0.131]), and recorded that
rather than adopting it.**

The author's own diagnosis, recorded seven times: *"I reach for the statistic that makes the result
look strongest among those I can defend in the moment, and I stop testing once it does."*

### 7.7 `arrow` was rejected — the `a apple` trap, walked into again

The fourth concept was first chosen as `arrow` on tokenization grounds (`[1,1,1,1,2,1]`, identical to
`bomb`). Its banks produced **8 prompt-family violations and 306 token-alignment violations** where
every previous bank had 0. Cause: **`arrow` is vowel-initial**, and the exact-word-swap invariant
substitutes it where `basket` stood after "a" — producing ungrammatical `a arrow`. This is precisely
the failure Part I recorded for the voided apple bank and that the Phase-5 plan explicitly names
(*"no grammar or tokenization asymmetries"*). *"It was written in the plan I am executing, and I
selected a vowel-initial word anyway."* Two fixes: `club` (consonant-initial, single-token, a fourth
genuinely distinct weapon category), and **`prompt_families.py --strict` from now on** — a flag that
already existed and was never being passed. Without it the generator prints `violations=8` and
**writes the bank anyway**.

⚠ **The "528 ungrammatical `a arrow`" count is now unauditable** (§11.2): the banks were deleted
before any grammar count was written to disk, and the surviving tokenization audit reports
`n_bad 0 / n_ambiguous 0 / concept_is_single_token true` — i.e. **the artifact that survives would
have passed the arrow banks.** The rejection is probably right; the evidence for it is prose only.
⚠ Also found by this audit: `prompt_families.py` **writes the bank to disk (line 896) before the
alignment check (913-918)**; `--strict` changes the exit code, not the write. Anything downstream that
keys off file existence rather than exit status can still consume a violating bank.

### 7.8 Two structural limits that no amount of compute fixes

* **The p-floor is set by the number of domains, not the sample size.** The exact paired sign-flip
  test operates on **6 domain clusters**, so its two-sided floor is `2/2⁶ = 0.03125` *no matter how
  many prompts each domain holds*. Every "p at the floor" in this window was floored by the design,
  not by n. **Adding prompts could never have fixed it** — which is why Phase 8 replicated across
  *banks* and Phase 10 across *pools*.
* **The bank tops out at 108 usable rows.** `behavioral + natural_doublespeak` is 468 rows, of which
  108 are in `core2x2 + slot3` and carry a demo block; 96 are used. The remainder are unusable
  (`strength` has non-empty `demo_block` on zero-demonstration rows — R-Z's trap) or are *different
  design factors* whose merger would repeat R-18's population contamination.

---

## 8. Cross-model findings that constrain everything else

**R-AU — attackability is a (bank × model) property, not a prompt property.** All banks share the same
96 `prompt_id`s, so this is directly comparable:

| pair | shared attackable prompt_ids |
|---|---|
| Llama `main` (22 successes) ∩ Llama `button_knife` (9) | **1** |
| Llama `button_knife` (9) ∩ **Qwen3** `button_knife` (6) — *same bank, different model* | **1** |
| Llama `main` (22) ∩ Qwen3 `button_knife` (6) | 3 |

**Two models on the identical bank agree on 1 of 9 attackable prompts.** This explains R-AT's Llama
null: of Llama's 20 down-flips on the main bank, only **1** is even baseline-successful on
`button_knife` — *"the knockout operates on a prompt set essentially disjoint from the one this bank
makes attackable."*

And R-AT's "null" is not inertia: **the knockout removed exactly 6 successes on both models; Llama
also gained 7 new ones.** A net of +0.0104 hides 13 changed rows. **On that bank the intervention is
destabilising rather than inert.** The log explicitly refuses the easy headroom explanation — Qwen3
had *less* headroom on the same bank (6 prompts vs 9) and flipped 6 of 6 to zero.

**R-AI — the one prediction that separates the two accounts.** The knockout masks whatever
demonstration block is present, so **a dose account predicts no relationship between the amount of
demonstration material and the size of the effect; a retrieval account predicts monotone growth.**

| | n=1 | n=2 | n=4 | n=8 |
|---|---|---|---|---|
| **Llama** baseline ASR | 0.1667 | 0.1667 | 0.2500 | **0.3333** |
| **Llama** knockout effect | −0.0833 | −0.1250 | −0.2083 | **−0.2917** |
| **Qwen3** knockout effect | +0.0417 ⚠ floor | −0.2083 | −0.1667 | **−0.3333** |

Llama is perfectly monotone in both columns and reaches the attainable floor (exact p = 0.0833 for 4
levels); Qwen3's `C_band` drives ASR to **exactly 0.0000 at every `n_examples` ≥ 2**. ⚠ Qwen3's n=1
row is a floor artifact (baseline exactly 0.0000). ⚠ The two models share a bank, so their p-values are
**not** combined. ⚠ This audit found the statistic is **mislabelled**: it is Pearson r on
log₂(n_examples), not Spearman (§11.1, defect 6).

---

## 9. WHAT WE DID NOT DO

* **No GCG/MAC objective was built.** Correctly: Part I's G4 null stands, and this window closed both
  remaining candidate quantities on evidence rather than exhaustion (§7.4). **Phase 7 is BLOCKED, and
  that is the recorded verdict, not an omission.**
* **No joint crossed bank.** Every crossed-design number comes from pooling **independently fitted**
  banks, so a "bank/pair identity" nuisance term (0.2783 of the spread) is inside the decomposition.
  One bank with all cells in a single row-set would remove it. Named as the stronger version, not
  built.
* **No fifth concept**, so "concept subspace is plane-dominated with a real PC3" is the strongest form
  available at K = 4 — four points span at most 3 dimensions. `arrow` showed that **concept selection,
  not compute, is the bottleneck.**
* **No Qwen3 replication of the geometry.** Every `x2fit_*` payload is
  `meta-llama/Llama-3.1-8B-Instruct` (the `model: null → PRIMARY_MODEL` default, resolved in the saved
  metadata). R-AD through R-BC are **Llama-only**.
* **No Qwen3 Phase-3 replication.** `refusalness:project_out:12-12` is Llama-specific; the Qwen3
  refusal directions on disk exist only at L20/L25/L28 (5120-d), so the composed spec hard-fails and
  must be re-specified. Recorded, not done.
* **Arm B (text-deletion ceiling) was deliberately not ported to Qwen3** (D-11) — a ceiling of one
  Bernoulli draw is not a ceiling on either model, and Phase 4 reports the arm-vs-control contrast,
  which needs no ceiling. Job 777122 was left to run so its refusal is *logged evidence* rather than an
  assertion.
* **The band-localisation question was closed as unresolvable**, not answered (D-12).
* **No third model family, no quantized variant** — still exactly two models, as in Part I.

---

## 10. Open items

1. **The Llama half of the magnitude claim.** Llama alone is p = 0.131 at k=18. A fourth pool
   (`club` corpus exists and is audited; only behavioural arms are missing) is the obvious next
   increment, and R-BB's machinery for pre-registering its outcome already exists.
2. **A bank-appropriate topicality instrument.** R-R's mechanism gloss is untestable because
   `goal_topicality` reads 0.0000 on the baseline by construction on a doublespeak bank. Until one
   exists, *what the suppressed completions actually contain* is unknown.
3. **A single jointly-fitted crossed bank** — removes the between-bank nuisance term from every
   geometry number in §6.4–§6.6.
4. **Qwen3 replication of the decomposition** (§6.5–§6.6 are Llama-only).
5. **The three `crossbank_knockout_test` run dirs without `DONE.json`** (6 of 9 complete) should be
   named or explicitly excluded by anything that globs that directory.
6. **The 18 failing tests at HEAD** (§11.3) — 12 of them are artifact-regeneration failures, i.e.
   *"the committed recipe no longer regenerates the committed artifact"*, which is exactly the standing
   bar Part I §11 (FM8) set.

---

## 11. Defects found by THIS audit (2026-08-24/25)

These are **new**. They are not in the project's own 17-correction registry. None overturns a
scientific conclusion in §6; all are quotation, metric-naming, provenance or coverage errors. Listed
so a reader of the primary log is not misled.

### 11.1 The eight upheld numeric/claim defects

| # | where | what the log says | what the artifact gives |
|---|---|---|---|
| 1 | **R-AE** variance accounting | codeword subspace (2 df) explains **0.5529–0.5722** | **0.5529–0.5714** over {L12, L14, L18}. Five different subspace definitions agree; 0.5726 occurs at **L20**, outside the section's layer set. The companion N-axis range 0.4290–0.4440 is **exact**. ⚠ Also: that N range is a *three-layer* range, not a band property — at L16/L17 it drops to 0.3937/0.3869 |
| 2 | **REVIEW-2 M3** mechanism | cells B and E are byte-identical across banks sharing a concept, `maxabsdiff = 0.000e+00` | True for **cell B** (both concept groups) and for cell E in the knife group, but **`basket_bomb`'s cell E differs by 7.81253e-04**. The *counts* (17 distinct, 7 duplicates, rank 16) are right **precisely because** that pair is not a duplicate — if the blanket claim held there would be 8 duplicates and rank 15. **The sentence explaining the result contradicts the result it explains.** |
| 3 | **R-T** | A→C and R→C+R are "both exactly **17 flips** of 96"; the knockout "removes the same ~17 prompts regardless of refusal state" | **Nets** are −17/96 in both (so the −0.1771 deltas are right). **Crossings** are **23** (20 down, 3 up) and **19** (18 down, 1 up), and the two down-sets **overlap in only 7** prompts. The additivity conclusion stands on the deltas; the per-prompt identity does not |
| 4 | **R-AB / R-AM / R-AN / R-AO / R-AP** | column headed **`uniq_frac`** | The metric is **distinct completion *lengths***, not distinct completions. All eight R-AB cells reproduce exactly as distinct `n_chars`; **none of the non-`C_all` cells reproduce if the text is hashed** — by text, Llama A and Llama C_band are **96/96 = 1.000 unique** (log: 0.875, 0.802), Qwen3 A 94/96, Qwen3 C_band 91/96, Llama C_all 24/96 (log: 0.229). `grep -rn uniq_frac` over `src/` and `scripts/` returns **nothing** — there is no code definition to appeal to. The headline is unaffected and if anything strengthened (`C_all` really is the only collapsed arm); the log's own prose (*"10 distinct completion lengths"*) is the accurate reading and its table header is not |
| 5 | **R-U** | demo tokens per row min/median/max **8 / 44 / 120** | **8 / 38.5 / 120.** Corroborated twice: all three Phase-4 Qwen3 runs' own `knockout_liveness.median_n_demo_positions` = **38.5** on that same population, and the log's own R-Q line prints 38.5. **44.0 is the median of the 8-row smoke** — copied across from the smoke table. Purely descriptive; nothing depends on it |
| 6 | **R-AI** | four "**Spearman ρ**" values; Qwen3 baseline **+0.8988** | The statistic is **Pearson r on log₂(n_examples)**, not Spearman. True Spearman gives Llama effect −1.0000 (p 0.0833), Llama baseline +0.9487 (p 0.1667), **Qwen3 effect −0.8000 and baseline +0.8000, both p = 0.3333** — so the two Qwen3 p-values quoted as 0.1667 become 0.3333 under the statistic the table names. The narrative claim (*Llama reaches the floor, Qwen3 does not*) survives either way. The value itself is 0.89868 → **0.8987**, a 4th-decimal slip |
| 7 | **Phase 6d** dose table | codeword **PC2** dose **0.0027** | **0.00203569.** The construction is pinned, not guessed — its singular² fractions reproduce the log's own Phase-6c row (0.4147/0.3146/0.2707) and its PC1 matches the direction the 777245 arm actually ran at `cos = +1.0000000`. Every other entry in the table reproduces exactly. Both values are "near zero"; the argument is unaffected |
| 8 | **R-AH / C-6** | "the R-AH runs record their real dose themselves via the C-6 code fix" | **2 of 9.** Only the two repair arms launched *after* C-6 (`p9Wlo` 777278, `p9Ulo2` 777279) carry `cell_residual_frac_removed`. The other seven carry `realized_dose` **without** it, so the five intervened arms' real doses (0.0831, 0.5484, 0.0982, 0.1241, 0.4138) are **offline recomputations from the fit payloads**. Every one of them reproduces exactly, so the science is unaffected — but *"recorded by the runs themselves"* is true of 2/9 |

**Five further apparent mismatches were adversarially refuted** — the log was right and the first
verifier looked in the wrong place. They are recorded because each names a convention the log never
states: R-BC's split-half ceiling **0.983–0.995** is right *at codeword × layer granularity* (the floor
is `button` at L12 = 0.983294) and not under cross-codeword pooling; R-AD's L10/L14 triples are the
**fraction-of-ceiling** column, not the raw cosines; the Gate-DOSE realized doses do come from a
**measured** quantity (`cellmean_frac_at_alpha1 = 0.8204430670353707`, shared by all 11 arms, confirmed
in-run by the three that record it) rather than from α; R-AI's −0.7208 is exact under the log's own
rounded-input pipeline; and R-BA's both-EOS **p = 0.0078** is the *cluster-level* version of that
control (T = −27, 8/8 informative, 190/768 rows — reproduced exactly), not the prompt-level one.
**One was superseded:** the F5 sentence pairing a percentile CI with a t-CI compares two different
populations, and R-BD had already retracted the percentile half four hours later.

### 11.2 Numbers with no artifact behind them

Nine claims could not be checked because nothing on disk computes them. They are not necessarily
wrong; they are **unfalsifiable as committed**.

| claim | status |
|---|---|
| R-AZ's **528 ungrammatical "a arrow"** (and "an arrow ×1180") | banks deleted before any grammar count was written; the surviving audit is silent on grammar and would have **passed** the arrow banks |
| C-15's correlation null (median −0.1200, 95% [−0.5377, +0.3153]) | no artifact, no code path computes a correlation null |
| R-BA's `P(no cluster nets the wrong way) = 0.9638`, and the sign-flip calibration FPRs **4.67% / 2.35%** | no calibration-simulation artifact exists |
| R-BB's power simulation (branch P = 0.999 / 0.921 / 0.980; refined 0.998 / 0.807 / **0.941**) | no simulation artifact or power code. Its internal arithmetic checks out, **but the stated within-cluster sd of 0.0626 does not reproduce**: pooling the 12 `pool × domain` clusters gives **0.0878**, which would roughly double the depth penalty |
| R-AV/C-13's `bank × domain` bootstrap CI lower bound **−0.1849** | 3 of 4 units reproduce exactly; this one comes out **−0.1875** (one grid step). Percentile endpoints depend on RNG feed order and no artifact stores this CI |
| REVIEW-1's "**77 tests pass**" | no artifact names that subset. At that commit `tests/` held 40 files / 587 test functions |
| whether any commit used `--no-verify` | git records no such flag; see §6.9 for what *is* determinable |

### 11.3 Coverage and provenance gaps

1. **The same silent-overwrite bug R-BD announced as fixed is still live in the same artifact.**
   `xb10final_.../summary.json` writes one `asr_<bank>` key per bank name with **no model in the key**,
   and every stored pair is the **Llama** arm (`asr_main [0.2292, 0.0521]` while Qwen3's `main` is
   0.1667 → 0.0). The commit fixed `cells[(model, bank, dom)]` and left the summary writer alone.
   No claim in §6.8 depends on those fields, but the artifact is self-inconsistent with its own
   `crossbank_test.json`. **The same file also records `"n_independent_pools": 5`, which is the count
   of distinct *bank names*; the true value is 3** — and the independence claim that licenses the k=18
   clustering rests on it being 3.
2. **Judge re-scoring instability is larger than any per-prompt argument in this window.** Sessions
   776893 and 777030 judged the **same generation files** for two arms. On byte-identical text,
   `p2A` returned an identical `strongreject_score` on only **70/96** rows and the same binary label on
   **78/96** — **18 of 96 prompts changed side of the 0.5 threshold on re-judging the same
   completion.** Both sessions nonetheless report the same aggregate ASR (0.2292): the flips cancel.
   **Point estimates are stable; per-prompt labels are not.** Any argument that leans on *which*
   prompts flipped (rather than on the net rate) is at or below the judge's own noise floor — which is
   the deeper reason defect 3 in §11.1 matters.
3. **18 tests fail at HEAD while `check_all` is green, and the pre-commit hook never runs pytest.**
   Six are "module imports without torch" tests, plausibly environment-shaped. **Twelve are not**:
   `tests/test_estimand.py` (5), `tests/test_g2_selection.py` (6) and
   `test_analyze_steering.py::test_T2_print_loop_key_and_json_written` — i.e. *"the committed recipe no
   longer regenerates the committed artifact."* If anything in the project says "all tests pass"
   alongside "check_all is green", **only the second is true at HEAD.**
4. **The unattributed third writer is invisible in git.** The log records `91e30a62` as belonging to
   neither session in contact and instructs treating the branch as having an unreachable writer. Git
   shows **all 113 commits with an identical author and committer identity and zero date skew**, so the
   anomaly exists only in the sessions' own accounts — and **further unattributed commits in the range
   cannot be ruled out.**
5. **`R-W` and `R-AC` have no persisted artifact and no script.** The per-bank arm/best-orth table, the
   12- and 16-cell crossed designs, the L12 spectrum, the variance decomposition and the
   arm-robustness sweep exist **only in the markdown**. `grep -rl 'pooled_cellmean_spectrum'` across
   `.py`/`.sh` matches nothing outside the log. All of them **do** reproduce from the `.pt` payloads —
   but only by re-deriving the method from the numbers. (Only R-H, R-K and R-M have artifacts.)
6. **`R-AC`'s decomposition is not a partition.** CELL 0.4055 + BANK 0.2783 + CONCEPT 0.1443 +
   CODEWORD 0.1331 = **0.9612**, and CONCEPT/CODEWORD are *nested inside* BANK rather than orthogonal
   to it. The rows should not be read as shares of one pie.
7. **`R-AD`'s table mixes two units.** "W var / N var" are projection fractions onto non-orthogonal
   unit directions, while "interaction" is a **norm** — so the row reads as a decomposition but sums to
   1.063. As an honest variance fraction the interaction is **0.0090 / 0.0032 / 0.0029 / 0.0011 /
   0.0018 / 0.0024** at L12/14/18/22/28/31, i.e. **the additive claim is stronger than its own table
   suggests.**
8. **No crossed bank is audited on both models.** The three older `x2` banks were audited on
   Llama-3.1-8B only and `button_bomb` on Qwen3-14B only. R-AC's gate row is literally accurate and
   reads as broader coverage than exists.
9. **Two different `button_bomb` fits are in circulation** — `buttonfit_20260821_150557_1157907`
   (used by R-H/R-K/R-M) and `x2fit_button_bomb_20260824_015451_272450` (R-AC's fourth crossed cell).
   Both are legitimate in their own family; nothing in the naming warns of it.
10. **`gate_dose_ladder.json` / `gate_e7_band.json` report a mean-*score* delta, not an ASR delta.**
    For the full-dose arm the file says `delta_pooled = 0.036111`, while the ASR difference the log
    quotes (**+0.036364**, 18/495 net flips) is correct but **appears nowhere in that artifact**.
    Anyone checking the log against the file will conclude the log is wrong. Relatedly, R-F's four-row
    dose ladder comes from `exp7_dsurface_add.json` (**L8, mode=add**, job 774835), not from job
    776397's L12 `project_out` session as its heading implies; and its correlations
    `r(dose, ΔASR) = −0.9775` / `r(frac_short, ΔASR) = −0.9623` are **score-based** — recomputed on
    binary ASR they are −0.9716 / −0.9702, which **reverses the implied ordering** of dose vs length.
11. **Three values of the dose constant `f` are in circulation** — run payloads 0.8204430670353707,
    `insubspace_null_full24.json` 0.8204428847812593, and C-2's quoted outputs back-solving to
    ≈ 0.82044273. All agree to 6 decimals, so every rounded claim survives, but **C-2's 15-significant-
    digit figures are false precision** — the digits past the 7th reproduce from nothing.
12. **Smaller items, each true but stated more broadly than the evidence:** R-E's "13 coherence files"
    is a filtered count (15 exist; two use an older schema with no `scorable_frac`); R-G's "seven-arm
    table" is 1 baseline + 6 arms; `pooled_cellmean_spectrum_{4,6}pair.json` both carry a verbatim
    stale caveat about *"pooling three separately-fitted banks"*; the log's median-character figures
    are **truncated, not rounded** (788.5 → "788"); R-L's "100%" is **8/8 prompts**; R-Z's "51–167
    chars" is 51–**170** on two of the four banks; and several line-number citations
    (`score_behavior.py:646`, `:468`, `:766`) are correct **at the pre-fix commit** and stale at HEAD
    (1174, replaced, 810).
13. **The two positive-delta arms are exactly the two with no cleanly-terminated prompts.** In
    Phase 10, `L|basket_gun` (+0.0104) and `L|button_knife` (+0.0104) both have
    `n_both_terminated = 0` (the gun arm: 86 of 96 baseline rows and 96 of 96 knockout rows
    truncated). This supports the log's "churn cell" framing, but it also means **the pooled mean is
    partly a function of which arms happened to terminate cleanly.** The both-EOS control (30/1) is the
    right guard and is reported.

---

## 12. How we worked — what this window adds to the error taxonomy

Part I §11 enumerated eight failure modes (FM1 dead guard, FM2 one-of-two-paths, FM3
unfalsifiable-by-inspection, FM4 mismatched footing, FM4b heterogeneous row set, FM5 instrument that
cannot represent the answer, FM6 silent failure, FM7 robustness checks that test the wrong thing, FM8
deliverable drifting from evidence). **All of them recurred here.** Four additions are new and
transferable:

* **FM9 — the saturated statistic read as strength.** A p pinned at its own attainable floor
  (`2/2^k`) carries no information about effect size, and *every* headline in Phases 2–4 was reported
  that way. C-14 caught it in a bootstrap tail; C-16 caught the identical thing rebuilt inside a
  permutation test *while explicitly trying to fix it*. **Standing check, now run by default: destroy
  the magnitudes, keep the signs, and see whether the p moves.**
* **FM10 — structure fitted to differences smaller than the measurement's own reproducibility.**
  Three layer laws in five hours (§7.5). The countermeasure is cheap and was adopted: **re-measure the
  same arm in a second session before fitting anything to the difference between two arms.**
* **FM11 — the uncomputed caveat.** C-15 was found by *computing a caveat the author had already
  written down in prose and left uncomputed while quoting the number it undermines.* **A caveat stated
  in prose is not a caveat until it is computed.** Notably the very next application of this rule
  moved a claim **upward** (R-BB-refined found its own hedge too pessimistic), so it is a discipline,
  not a bias.
* **FM12 — the metric that is not the metric it is named.** `uniq_frac` is distinct completion
  *lengths*; `dose` is a *variance* in one place and a *norm* in another; `Spearman ρ` is Pearson r on
  a log axis; `delta_pooled` is a score delta in an ASR table. Four instances in one window, each
  harmless alone and each capable of inverting a comparison. **Name the estimand in the field name.**

**Two disciplines from this window worth keeping outright.** First, **pre-registration that is
actually scored**: R-BB registered P = 0.941 with a stated mechanism, the interim explicitly
**declined to compute the favourable-looking subset early** (*"computing it now is the failure mode
C-17 named, and this is the first time in this phase I have had the opportunity and declined it"*),
and R-BD scored the prediction against the real outcome rather than re-deriving it after. Second,
**two independent computations of the same number**: R-BD's silent-overwrite bug was caught *only*
because a tool and a hand-written snippet were compared — *"the tool alone would have shipped a
plausible wrong number, and the artifact would have made it look authoritative."*

---

## 13. Where the project stands

**Plan §18's four-way label, restated for this window.** Part I's answer was **C, amended** — a
refusal-only story with a small second channel. That verdict is unchanged for `d_surface`, and this
window strengthens it: the second channel is now shown to be **dose, not direction**, on a bank built
specifically to give direction a chance.

**But the object of study has moved.** The surviving mechanism is not a direction at all:

> **Demonstration retrieval is causally necessary for the doublespeak jailbreak.** Masking the
> generated answer's attention to the demonstration block across a mid-stack band (Llama L6–14,
> Qwen3 L7–17 — the same 0.19–0.44 of depth) suppresses attack success by **−0.1771 / −0.1667** on the
> high-headroom bank of each model, against an identically-key-matched late-layer control that is
> nearly inert. It is **independent of the refusal channel**, **monotone in the number of
> demonstrations** on both models, **redundant across layers** (all 40 heads of one layer are
> dispensable), and it **fits no direction, so no dose confound is possible**. Across 3 demonstration
> pools, 5 banks, 2 models and 10 populations: **113 prompt-level down-flips against 30 up**
> (p = 1.577e-12), and **30 / 1** among rows where both arms terminated on EOS (p = 2.98e-08).
>
> ⛔ **Amended by C-18:** the sentence that stood here — *"and a calibrated cluster interval of
> Δ = −0.0764, CI95 [−0.1459, −0.0069], which excludes zero"* — **is withdrawn.** That unit is a
> crossed table on one shared prompt set; both its marginals include zero. **No calibrated cluster
> test of magnitude excludes zero.** The direction above is what stands, and it is carried by Qwen3 —
> **Llama alone remains p = 0.131**, and every leave-one-out drop removes the exclusion.

**What that does not license.** It is not an optimization objective: every attempt to reduce it to a
scalar failed, and the most natural candidate (attention mass to the demonstrations) **anti-predicts
causal importance on the second model**. It is not a mechanism story either — what the suppressed
completions contain is uncharacterised, because this bank has no instrument that can tell. And the
representational object the sprint was named after (`d_surface`, now decomposed into a codeword
subspace and a plane-dominated concept subspace, both beautifully reproducible at the split-half
ceiling) has **no demonstrated causal role in the behaviour at all**.

**The one-line handover:** *the representation is real and measurable, the behaviour is causally
attackable, and after nine days the two still do not meet.*

---

## 14. Reproducing this

Python: `/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`
(torch 2.7.1+cu126, transformers 5.12.1, scipy 1.17.1, sklearn 1.9.0). **The login shell's default
python has no torch**, so `pytest tests/` errors at collection on 13 files. All analysis in §6 is
CPU-only.

```bash
# the six deliverable guards (all must exit 0)
python src/boombness/check_all.py

# the knockout instrument, CPU-only, ~26 s
pytest -q doublespeak_causality/tests/test_allquery_attnknockout.py \
          doublespeak_causality/tests/test_attnknockout_synthetic.py

# this window's guards, ~4 s
pytest -q tests/test_knockout_liveness_gate.py tests/test_band_range_and_abort.py \
          tests/test_knockout_heads.py tests/test_commit_guard.py \
          tests/test_crossbank_stratification.py

# install the commit guard (blocks a commit while check_all is red)
bash scripts/install_commit_guard.sh
```

**Intervention grammar:** `name:mode:lo-hi:alpha`, `+`-joined for composed arms, band **inclusive**
(`range(lo, hi+1)`, `score_behavior.py`). Arms are submitted as

```bash
sbatch --export=ALL,BOOMB_SCRIPT=score_behavior.py,BOOMB_ARGSFILE=$REPO/outputs/boombness/argsfiles/<NAME>.txt \
       src/boombness/slurm/run_boombness.sh
```

⚠ `outputs/` is gitignored, so **every argsfile of this phase is outside version control**; the phase
log embeds the literal strings (its §"REPRODUCIBILITY GAP CLOSED") and is the only durable record.
⚠ `config.json` records `"attn_impl": "sdpa"` for knockout arms because the flag is omitted;
`score_behavior.py` forces **eager** whenever a knockout is requested, and `metadata.json` carries the
truth. **Every Phase-2/3/4 arm actually ran eager, bf16.**

### Canonical artifacts of this window

| artifact | holds |
|---|---|
| `outputs/boombness/crossbank_knockout_test/xb10final_20260824_230323_1997748/crossbank_test.json` | **the final causal result** — 10 populations, 3 pools, 2 models, k=18 |
| `outputs/boombness/crossbank_knockout_test/xb8_20260824_192145_1606684/` | the 8-population predecessor ⚠ its `cells`-based statistics are model-collapsed and superseded |
| `outputs/boombness/crossbank_knockout_test/xbtest{,2}_20260824_11*` | Phase 8, Qwen3-only, thresholds 0.25/0.50/0.75 |
| `outputs/boombness_followup/gate_dose_ladder.json` | Gate DOSE, 14 arms, one session, n=495 |
| `outputs/boombness_followup/gate_e7_band.json` | Gate E7, 7 arms, one session, n=495 |
| `outputs/boombness/judge/{p2j,p3j,p4j,p4hj}_*` | Phases 2/3/4 — sessions 776893, 777030, 777134, 777118 |
| `outputs/boombness/extract_boombness/x2fit_*` (12 dirs) | all geometry in §6.4–§6.6; `directions_fit_{dev,heldout}.pt`, `layer_convention = block_L == hidden_states[L+1]`, `position = codeword_last`, `n_per_cell = 30` per cell |
| `outputs/boombness/pooled_cellmean_spectrum_{,4pair,6pair}.json` | R-H / R-K / R-M ⚠ carry a stale 3-bank caveat |
| `outputs/boombness/retrieval_strength/rs{Llama,Qwen3}{,H}_*` | R-AJ / R-AK / R-AL |
| `outputs/boombness/p2_instrument_generation_change.json` | R-L, the instrument proof (n = 8) |
| `doublespeak_causality/pair_common.py:495` | `AllQueryAttentionKnockout` — the instrument this window had to build |

### Source documents

| document | lines | status |
|---|---|---|
| `reports/SPRINT_SUMMARY_2026-08-16_TO_08-23.md` | 851 | **Part I** — the state this document continues from |
| `external_md/BOOMBNESS_DSURFACE_NEXT_PHASE_PLAN_AND_PROGRESS.md` | 6,029 | **CURRENT** — this window's live log. Read its LIVE CLAIMS LEDGER (top) before quoting any figure from it |
| `external_md/BOOMBNESS_D_SURFACE_FOLLOWUP_PROGRESS.md` | — | the previous phase's live log; superseded for everything this window touched |
| `reports/boombness_objective_sprint_report.md` | — | the main report; §0a is the one-screen state |
| `docs/BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md` | 1,208 | the original plan (2026-08-16) |

---

*Compiled 2026-08-24/25 at HEAD `8c83c8f3`, working tree clean. 361 numeric and source-level checks
were run against the committed artifacts: 338 matched, 8 defects survived adversarial re-derivation
(§11.1), 9 claims have no artifact behind them (§11.2), and 13 further coverage or provenance gaps are
recorded in §11.3. Where this document and the project's own prose disagree, the artifact was
followed.*
