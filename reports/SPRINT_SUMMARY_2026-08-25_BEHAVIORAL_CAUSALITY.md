# Sprint summary — Demonstration Retrieval → Behavioral Causality (2026-08-25)

**Branch:** `behavioral-causality-sprint` · **Live log:** `external_md/DEMONSTRATION_RETRIEVAL_BEHAVIORAL_CAUSALITY_NEXT_PHASE_PLAN_AND_PROGRESS.md` · **Handoff:** `RESEARCH_HANDOFF.md`

Self-contained: no session context required. Where this disagrees with any earlier report, **this and
the live log win** — several framings produced *within this phase* were later withdrawn by this phase,
and §6 lists them so they are not revived.

---

## 1. Starting state

The prior sprint had closed the `d_surface` "bombness direction" as an attack objective and concluded
that **refusal-suppression, not the concept representation, is the causal locus**. It had also shown a
demonstration-attention knockout removes the doublespeak attack, but with **one unscoped mask** —
every query row attending to the demo block — so it could not say *which part of processing* mattered.

## 2. What this phase set out to do

Determine what the surviving causal mechanism actually is, connect it to behaviour if possible, and
produce a defensible result. Concretely: decompose the knockout by **which query rows** it applies to,
and test whether the surviving effect is demonstration-specific, mechanistically explained, and
replicable.

## 3. The instrument

Five scopes over the same key set (the demonstration block), differing only in which **query rows**
are masked: `legacy_all_query` (the original, unscoped), `query_prefill_only`, `demo_processing_only`
(demo→demo during prefill), `response_query_only`, `decode_only`. Every arm carries a **liveness
contract** — required-positive and required-zero edit counters — so a null can never be reported
without proving the intervention fired.

**Population:** a 10-domain bank (4560 rows; behavioural filter → **160 rows = 10 domains × 16**),
`natural_doublespeak`, `n_examples ∈ {1,2,4,8}`. **Models:** Llama-3.1-8B-Instruct and Qwen3-14B.
**Judge:** StrongREJECT pinned to `openai/gpt-4o-mini`. **Refusal:** `kw_refusal`, a deterministic
keyword detector — **not** the LLM judge, so it carries none of its measured session drift
(78/96 binary agreement across sessions).

## 4. Exact experiments run

| # | Experiment | Jobs | Outcome |
|---|---|---|---|
| 1 | Scoped decomposition, Llama, 10 domains | 779915-779919 + judge 779926 | R-19 |
| 2 | Scoped decomposition, Qwen3 | 779947-779951 + judge 780012 | R-20 |
| 3 | Within-family binding bridge, both models | (analysis only) | R-16, R-17 |
| 4 | Kill-route breakdown, 8 cells | (analysis only) | R-21 |
| 5 | Dose-response by `n_examples` | (analysis only) | R-22 |
| 6 | Dose-matched refusal-vs-ASR | (analysis only) | R-23 / C-12 |
| 7 | Non-demo control — strict | smoke 780231, arms 780297-780299 | **all refused; R-24, R-25** |
| 8 | Non-demo control — capped ×3 draws | 780300-780302 + judge 780390 | R-26 |
| 9 | Fourth independent pool, Llama | pool 780821, audit 780879, arms 780892-780895, judge 780928 | R-29 |
| 10 | §20 Q3 rescue: instrument build + identity control | smoke 781006/781047/781168 | R-30…R-34 |
| 11 | Rescue sweep, Llama pool A (+ below-band control) | 781211/781212, judge 781255 | R-35 |
| 12 | Rescue, Qwen3 pool A | 781290/781291, judge 781361 | R-36 |
| 13 | Qwen3 ASR-rescue confirmatory test, pool B | 781410-781413, judge 781548 | **R-37 (does not confirm)** |
| 14 | Rescue, Llama pool B — completes the 2×2 | 781643/781644, judge 781727 | R-38 |

## 5. Where we won

**W1 — `demo_processing_only` uniquely restores refusal, in three independent settings.**

| setting | model | pool | baseline refusal | `demoproc` rise | other scopes |
|---|---|---|---|---|---|
| 1 | Llama-3.1-8B | A | 0.0563 | **+0.1625** | all within margin |
| 2 | Qwen3-14B | A | 0.0125 | **+0.1312** | all within margin |
| 3 | Llama-3.1-8B | B | 0.0063 | **+0.1938** | all within margin |

Killed-by-refusal: **14/25, 8/20, 9/24** for `demoproc`; **0, 0, 1** for the controls. Pre-registered
twice before reading (**PR-6** 3/3 conditions, **PR-12** 2/2). Pool B shares **0 of 40** sentence sets
with pool A.

**W2 — the concept binding SURVIVES the intervention, within the same demonstrations.** Each family
contributes one behavioural row and one probe row sharing a byte-identical demo block. Llama: `demoproc`
loses binding on **0 of 48** families while killing 7 attacks. Qwen3: **0 of 10** killed families lost
binding, while the same arm *did* cost binding on 5 families whose attack survived — so the arm is
capable of damaging binding and simply never does so where it disarms. `legacy` flattens **28/48**.

**W3 — attack removal is coherent non-compliance, not generator collapse.** **0 degenerate rows in 165
killed attacks across 8 cells**, `frac_scorable = 1.000` everywhere. Detector mutation-verified (fires
on repeated-phrase/single-word text, not on coherent prose); worst real row scored `uniq_word_ratio`
**0.640** against a 0.45 threshold.

**W4 — the four scopes are statistically indistinguishable on ASR.** All pairwise gaps ≤ the
pre-registered 0.0417 margin except marginal `qpre` pairs. This is the **control that makes W1
meaningful**: same attack removed, different route.

**W5 — the dissociation is CAUSAL, and it replicates across a complete 2 × 2.** A per-position
activation patch that hands back the clean demonstration activations at the top of the knockout band
removes **58-92%** of the refusal rise in **all four** model × pool cells (gaps 0.1125 / 0.1062 /
0.0750 / 0.1125, every one clearing the 0.0521 margin) — **while leaving the attack removal intact on
Llama** (recovers only 16.7%, inside the margin). The **below-band control at the same positions moves
refusal by exactly 0.0000 in all four cells**, and the identity control (`--rescue-donor self`)
reproduces its own arm **8/8 byte-identical**. **One intervention gives back the refusal and not the
attack.**

**W6 — raising domains 6 → 10 made the sign test a real test.** At k=6 the attainable floor was 0.0625;
at k=10 it is **0.00195**, and `demo_processing_only` on Llama is negative in **all ten domains**.

## 6. Where we failed, and what we withdrew

**F1 — the mechanism we thought we had is not the mechanism (C-12 / R-23).** *"`demo_processing_only`
works BY restoring refusal"* is **withdrawn**. At matched dose (Llama `n_examples`=4) all three arms
removed the same 7 of 8 attacks — gaps **0.0000** — while one restored 9 rows of refusal and two
restored none. On Qwen3 at n=8 the refusal-restoring arm removed **less** (−0.1500 vs −0.2000). The
restoration is a **second, distinct effect**, not the route.

**F2 — demonstration-specificity is not constructible on this bank (R-25).** A count-matched non-demo
control needs as many maskable non-demo positions as the demo block. The demo block grows
**12 → 106 tokens**; the unprotected non-demo pool is near-constant at **~53**. `match_ratio` is
**1.0 at n_examples=1** and **0.0 at 4 and 8**. Rescoping to feasible rows is forbidden — demo length
*is* the dose. **Branch stopped, not rescued.** One suggestive cell survives (R-26: at n=2, where the
capped draw is 0.989-matched, `demoproc` removed 5/5 attacks vs the control's 0.67/5, gap 0.1083).

**F3 — the mapping-usage question is unanswerable with this bank (R-27).** Concept usage collapses from
64%/81% (baseline jailbroken) to 0-11% (killed) — but baseline **non-jailbroken** rows sit at 6%/10%.
In this bank "mentions bomb" ≈ "is a jailbreak", so the measure is confounded with the outcome.
**Reported as an instrument failure**; no mapping-usage claim made.

**F4 — dose-response is single-model (R-22).** Llama is textbook (+0.0000 → +0.3500, monotone, 6.7×
margin; **exactly zero at n=1**, so the effect needs *accumulated* demonstrations). Qwen3 is
non-monotone with endpoint +0.0250, **inside the margin — refuted by the pre-registered rule.**

**F5 — the ASR rescue failed its own confirmatory test.** A Qwen3 ASR rescue appeared on pool A
(+0.0625, above margin) and **missed the pre-registered threshold on pool B** (+0.0437, needed
>0.0521 — short by ~1.3 rows of 160). It was **recorded as an unregistered observation and never
claimed**, so this is a non-event rather than a retraction — **which is the entire point of having
declared the ASR column irrelevant before seeing it.**

**F6 — two §20 questions were never run:** its low-rank follow-up (Q4) — now differently motivated,
since there is no successful ASR rescue to decompose — and the joint crossed Qwen3 factorization (Q6),
dropped as no longer justified by current evidence.

## 7. Corrections issued against our own work

| # | What | Impact |
|---|---|---|
| C-10 | Expanding `DOMAINS` 6→10 broke regeneration of the **canonical** bank (`KeyError: 'warehouse_logistics|benign'`). Caught by a test going red, not by inspection. | Fixed by deriving domains from the pools file; both banks now verified **byte-identical** on regeneration, with a new test asserting it |
| C-11 | I ranked arms by an ASR ordering **inside my own 0.0417 margin** — in the document that defines the margin | Ranking withdrawn; the refusal contrast (order-of-magnitude clear) is what carries |
| C-12 | See F1 | Headline mechanism withdrawn |
| R-19 | Outcome B (`respq` a "weak partial", 46% of legacy) does not replicate at k=10 (85%, gap 0.0188) | Withdrawn rather than resolved by picking a bank |
| R-32 | I built `DonorPatch.liveness()` and **never recorded it** — the smoke completed cleanly and could not prove the patch had fired | Wired onto every row + a test asserting it is *called* **and** *recorded*; smoke re-run |
| DR-3 | Donor capture was placed **above** the line building `ctxs` — Python would not raise, it would silently read the **previous row's** hooks | Moved after `ctxs`; a **static** regression test guards source order, since no row-level test could |
| DR-4 | Published 92.4% for pool B; row-exact is **92.3%** (rates were rounded before dividing) | Corrected in place in log and handoff |
| DR-2 | Every ASR is over **192-token completions**; Llama baseline is **58%** truncated, `demoproc` **73%** | No number retracted; the **scope** of "ASR" is now stated. Qwen3 (26% truncated) has both-EOS subgroups of 111/114 rows where every effect survives at full size |

## 8. Final claims

See `RESEARCH_HANDOFF.md` §4 for the full table with n, independence unit, test and artifact.
Summary: **C1 confirmatory** (3 settings) · **C9 confirmatory** (4/4 cells, causal) · **C2, C3, C4, C5
replicated** on two models · **C10 instrument-verified** · **C6, C8 single-model** · **C7 unresolved**.

> **Doublespeak's demonstration block does two separable things. Masking demo→demo attention during
> prefill removes the attack *and* restores refusal — and the second does not cause the first. The
> concept mapping survives the intervention that removes the behaviour. Handing the demonstration
> activations back gives the refusal back without giving the attack back, in all four model × pool
> cells, while a below-band control at the same positions does exactly nothing.**

## 9. Limitations

1. Demonstration-specificity untestable where the effect lives (F2) — **needs a longer-context bank**.
2. Mapping usage unreadable (F3) — **needs a benign-register concept vocabulary**.
3. All ASR is over the first 192 tokens (DR-2).
4. `kw_refusal` is lexical: it detects refusal *markers*, not refusal.
5. Lexical generality G = 1 (one codeword) throughout this phase.
6. Coherent non-compliance is a **residual** category and is not itself explained.

## 10. Canonical artifacts and reproduction

Full artifact paths, the reproduction manifest (one command per result), and the repo hazards worth
carrying forward are in **`RESEARCH_HANDOFF.md` §8-§9**. Judge provenance is closed on every
behavioural result (`judge_model_used` and `completion_sha256_16` on 100% of rows); bank provenance is
verified at **content level** via per-row `prompt_sha16` on **13/13** pool-A arms.

**Test suite at close: 1358 passed, 7 skipped, 0 failed** (serial and exclusive — concurrent runs
corrupt committed artifacts, see C-2).
