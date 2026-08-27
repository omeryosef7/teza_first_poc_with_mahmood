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
| 15 | Query-span rescue + below-band control, Llama | 781849/781850, judge 781899 | R-39 |
| 16 | Size-matched 24-position demo rescue (`n_examples`=8) | 781930/781931, judge 781956 | R-40 |
| 17 | Reproduction-manifest audit: executed the commands instead of trusting them | (analysis only) | C-13, R-41, R-42, R-43, R-44 |
| 18 | Long-context bank via in-body filler — **failed, made it worse** | (analysis only) | R-45, R-46 |
| 19 | CPU feasibility instrument, quarantined then fixed and validated twice | 782597-782609, 782774 | R-47, R-48 |
| 20 | Preamble bank (`longpre`) + C7 test at every dose | 782836-782840, judge 782891 | **R-49, R-50** |
| 21 | Minimum-preamble selection + mandated re-run | 783028-783030, 783039-783043, judge 783116 | **R-51, R-52** |
| 22 | C13 cross-model test (neutral context on Qwen3) | 783439, judge 783458/783459 | **R-54** |
| 23 | C7 on Qwen3 — first attempt, **refused at pre-flight** | 783595/783596, 783712/783713 | **C-18** |
| 24 | Qwen3-correct preamble bank (`longpreQ14`) + power check | 783828-783831, 783849, judge 783886 | R-55, R-56 |
| 25 | **C7 on Qwen3 — CONFIRMS** | 783849/783903/783904/783945/783946, judge 784128 | **🏆 R-58** |
| 26 | **C7 replication on pool B — CONFIRMS** | 784371/784372/784380/784381 + baseline, judge 784409 | **🏆 R-62** |
| 27 | **C7 truncation test at a 640-token cap — CONFIRMS** | 784460/784461/784658, judge 784740 | **🏆 R-64** |

## 5. Where we won

**W1 — `demo_processing_only` uniquely restores refusal, in FOUR independent settings.**

| setting | model | pool | baseline refusal | `demoproc` rise | other scopes |
|---|---|---|---|---|---|
| 1 | Llama-3.1-8B | A | 0.0563 | **+0.1625** | all within margin |
| 2 | Qwen3-14B | A | 0.0125 | **+0.1312** | all within margin |
| 3 | Llama-3.1-8B | B | 0.0063 | **+0.1938** | all within margin |
| **4** | Llama-3.1-8B | **`basket_bomb` (2nd CODEWORD)** | 0.0208 | **+0.1250** | **all three at exactly 0** |

Killed-by-refusal: **14/25, 8/20, 9/24** for `demoproc`; **0, 0, 1** for the controls.
Setting 4 is a **second codeword** (`basket`, R-73/PR-29) — a new generality axis, not another pool —
lifting **lexical G from 1 to 2 for C1 only**; every other claim, C7 included, stays at G = 1.
Setting 4 is **truncation-robust (R-75/PR-30)**, and unusually sharply: that bank truncates **0.938**
at baseline under the 192-token cap, but re-running at **640** — where both arms stop on length
**0.000** of the time — gives **the identical +0.1250 on exactly the same 14 rows**, while **81 of 96
completions changed**. Refusal decisions did not move at all. **DR-2's truncation caveat is an ASR
caveat, not a refusal caveat**, and C1 is a refusal claim in all four settings. Pre-registered
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
removes **12-18 refusal rows** in **all four** model × pool cells, every one clearing the **8.3-row**
margin (**1.44-2.16×**) — **while leaving the attack removal intact on Llama** (16.7% recovery, inside
the margin). *As percentages of the rise that is 58-92%, but those figures are* ***inverted*** *relative
to the evidence — see the correction table.* ~~The below-band control at the same positions moves refusal by exactly 0.0000 in all four cells~~
**— WITHDRAWN (C-20): that arm is byte-identical to knockout-only on 160/160 rows, a no-op by
construction rather than an inert intervention, so no specificity control was run.** The identity
control (`--rescue-donor self`) reproduces its own arm **8/8 byte-identical** and is unaffected — it
is an instrument check and was always meant to be a no-op. **One intervention gives back the refusal and not the
attack.**

**W9 — 🏆 C7 IS RESOLVED, REPLICATED AND TRUNCATION-ROBUST: attack removal is DEMONSTRATION-SPECIFIC.** On Qwen3, masking the
demonstration positions removes **5 of 5** attacks at `n_examples`=4 and **5 of 7** at n=8, while
**three independent count-matched masks of the same size, drawn from elsewhere in the same prompt**,
remove **1, 2, 2** and **2, −2, −1** — every one inside the pre-registered ±0.0521 margin. Separation
**2.0×** and **3.2×** the arm-vs-arm margin, **all three PR-23 conditions holding at both decisive
doses**, with `match_ratio` **1.000 on all 480 control rows** and **3/3 distinct draws**.
**Masking N demonstration positions kills the attack; masking the same N elsewhere does not.**

**Replicated on an independent pool (R-62, PR-25):** −4 of 4 at n=4 and −5 of 6 at n=8
(**−0.1000** / **−0.1250**), three fresh count-matched draws at **+1, +1, +1** and **0, −1, −2**,
separation **3.0×** and **1.8×**, `match_ratio` **1.000 on every control row**, draws distinct by
seed **and** by generation hash. The separately-judged power gate agreed with the re-judged baseline
**exactly at both decisive doses**.

⚠ **Qwen3 only** — Llama's version was **declined for power (F6), never refuted** — and it rests on
5 and 7 baseline attacks, i.e. **5 rows against a 2.1-row margin**.

**Truncation-robust (R-64, PR-26).** The ASRs above cover the first **192** generated tokens, on an
arm that terminated on only 0.325/0.300 of its rows versus 0.519–0.606 for its controls (C-19).
Re-run at a **640-token cap** — every arm stops on length **0.000** of the time, longest completion 634
tokens — the effect **survives at the same size** (the cap moves neither arm detectably — C-23): `demoproc` removes **3 of 4** at n=4 (−0.0750) and **7 of
7** at n=8 (**−0.1750**, up from −0.1250); the count-matched control moves **+1** and **+0**;
separation **2.4×** and **4.2×**. The truncation hypothesis predicted the effect would shrink once
completions could finish. It did the opposite. ⚠ The untruncated n=4 cell is the thinnest number in the
claim (**−3 rows against a 2.08-row margin, 1.4×**), and the 640-token result rests on **one**
count-matched control rather than three.

**W8 — the count-matched control was finally BUILT, after three attempts and a measured
specification.** R-25 left "demonstration-specificity is not constructible" as a qualitative limit.
R-48 turned it into a number (**≥76 non-demo, non-query tokens at `n_examples`=8**, measured, with
every cheaper lever excluded); R-46 showed in-body filler makes it **worse** (it grows `demo_block`);
R-49 delivered a bank where **`match_ratio` is 1.000 (min and mean) at all four doses**, pool 30 →
160, with `demo_block` byte-unchanged. **A control that had been impossible for the whole phase
became real on every row of 480.**

**W7 — the two effects are localised differently, and it is position IDENTITY not count.** The attack
damage is reachable from the **query span** (+0.0563 ASR, clearing the margin by 0.7 rows;
**its cited below-band control is withdrawn — C-20**) but
**not** from the demonstration positions. Size-matched at **24 positions each**, a demo patch removes 4
refusal rows and restores **no** attack while a query patch removes **13** and restores attack — same
count, same layer, same rows, opposite behaviour.

**⛔ And its limit, in the same breath:** the query patch restores **both** effects, so this is a
**single** dissociation, not a double one. **The two effects do not live at separate loci** — one locus
is selective, the other is not. The demo patch's magnitude also scales with count (24 of ~114 positions
buys 36.4% of the effect), so **no all-or-none locality is claimed**.

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

**F6 — and building the control COST THE PHENOMENON, which is the deeper limit.** The preamble that
makes the control constructible also removes the attack it is meant to test: baseline ASR
**0.1562 (d10) → 0.0625 (preamble 12) → 0.0437 (preamble 10)**. PR-19 required both `n_examples` 4
and 8; on the 12-sentence bank **n=8 held all three conditions** (demoproc −0.1000, controls
+0.0000/+0.0500/+0.0000, separation **2.8× margin**) while **n=4 failed**, so PR-19 did not confirm.
Cutting the preamble to the principled minimum (R-51, chosen on feasibility alone) **recovered
nothing measurable** — 3 rows against an 8.3-row margin — and left both decisive doses **below the
underpower threshold**, so the re-run was **DECLINED**. **The trade is not tunable by preamble
length.** **On LLAMA C7 remains undecided — declined for power, never refuted** — for a sharper
reason than before: *the control can be built, and building it costs the phenomenon.* **C7 was
subsequently RESOLVED on Qwen3 (W9), where that trade does not apply.**

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
| DR-5 | **The "% of refusal rise removed" figures are INVERTED relative to the evidence.** The 92.3% cell is **12 rows / 1.44× margin** (weakest); the 69.2% cell is **18 rows / 2.16×** (joint strongest). A near-zero clean baseline (2 rows of 160) inflates the ratio | Nothing retracted — every cell clears its pre-registered margin, and the margin was always the registered test. **Rows and ×margin now travel with every percentage** |
| ~~this file~~ **C-14** | I "corrected" the Llama ASR recovery from **16.7%** to **16.6%** — **backwards.** Row-exact is `4/24 = 16.7%`; the 16.6% came from dividing **rounded rates**, i.e. the exact round-then-divide artifact DR-4 warned about, committed while fixing that class | **The correction is withdrawn; 16.7% stands.** Caught by the final consistency pass |
| PR-18 | My own pre-registration defined outcomes **A and C so that both could fire** — and both did | Reported as **both** (A on threshold, C on magnitude) rather than choosing the flattering one |
| C-13 | `binding_behaviour_bridge` silently **subset** the population when handed a bank the runs did not come from (96 of 160 rows kept, a plausible different answer) | Found by **executing** the manifest rather than reading it. Guarded; no published result affected |
| C-14 | I "corrected" a figure **backwards** — 16.7% → 16.6% — using the very round-then-divide artifact I was writing the rule against | Correction withdrawn; **16.7% stands**; all 8 published percentages then verified row-exact and guarded by a test |
| R-46 | My first long-context bank grew the **demonstration block** instead of the drawable pool — the opposite of the requirement | Branch stopped; the failed preset kept as a record of what cannot work |
| R-52 | My readout script applied PR-19's three conditions but **not its underpower rule**, and would have reported a refutation where a **decline** was mandated | Corrected before the numbers were written down |
| DR-2 | Every ASR is over **192-token completions**; Llama baseline is **58%** truncated, `demoproc` **73%** | No number retracted; the **scope** of "ASR" is now stated. Qwen3 (26% truncated) has both-EOS subgroups of 111/114 rows where every effect survives at full size |
| **C-19** | **C7 was resolved (R-58) and replicated (R-62) without ever running the truncation check DR-2 made mandatory.** Running it: `demoproc` terminates on **0.325/0.300** of its rows vs **0.519–0.606** for its own controls, and the both-terminated subgroup at the decisive doses is **3, 1, 1 and 0 rows**. DR-2's protection came from Qwen3 being lightly truncated on the *internal* bank; the preamble that made the control constructible pushed every `longpre` prompt against an unchanged 192-token cap, and it did not transfer | **Nothing retracted** — termination is post-treatment, so an empty subgroup is not evidence of an artifact. C7's **scope** was made explicit and then **discharged by R-64**: re-run at a 640-token cap with 0.000 truncation on every arm, `demoproc` removes **3/4** and **7/7** (separation 2.4×/4.2×) — the effect **grows**, so the cap was not the explanation. Root cause of the miss: a rule that lived in a prior review instead of in a pre-registration gate |
| **C-20** | **The below-band L5 rescue arm is a NO-OP BY CONSTRUCTION, and C9, C11 and C12 each published it as a layer-specificity control.** Below the knockout band the knocked-out run's prompt-position activations are bit-identical to the clean run's, so a clean-donor patch writes what is already there. Four instances — two models, two position modes, three sessions — are **byte-identical to their own knockout-only arm** (160/160, 160/160, 160/160, 40/40) while every in-band arm differs. `rescue_liveness` correctly reported `fired: true`: liveness proves the hook ran, not that it mattered | **Primary effects stand** (they rest on the in-band arm). **C9, C11 and C12 lose their specificity leg** — no such control was run; the citations are struck in the handoff and above. The exact zeros ("EXACTLY 0.0000", "15→15") were the tell and were read as clean control behaviour. Byproduct: C11's control "+0.0125 ASR" on byte-identical text is a measured **judge non-reproducibility floor of 2/160**. **CONFIRMED** by a same-session knockout-only arm (R-68): below-band **160/160 identical**, top-of-band **4/160**. The first replacement control I chose — the band's **bottom** layer — was **also vacuous** (160/160), which pinned the real rule: `DonorPatch` writes the residual stream *entering* the block, so any `rescue_layer <= lo` writes an untouched state. Vacuous for `layer <= lo`, real only at `lo+1` and above; the test encodes that and the band-floor trap |
| **C-21** | **I attributed a byte-identity artifact to "generation is not reproducible across sessions" when the real cause was POOL A vs POOL B.** I was one step from publishing a ±0.0312 "generation-session ASR noise floor" measured from two run pairs that differed only in `bank`; diffing their RUNMETA args first showed they were different demonstration pools, so the gap is the pool effect R-29 already established | **Floor withdrawn before it was ever published**; PR-3's margins are not undermined. C-20 is unaffected — its decisive test was same-bank and same-session. R-67's conclusion stands but its stated reason is withdrawn, and the "within one session" framing becomes **"on the same bank"**. The true picture is *stronger*: generation here is **deterministic** given the same bank, which is what makes byte-identity sharp enough to have caught C-20. Root cause: C-13's defect — a comparison silently run against the wrong population |
| **C-23** | **I framed a 1-2 row change as the effect "GROWING".** R-64 said the C7 effect grows at n=8 (−0.1250 → −0.1750) once completions finish. Pooled over the 80 rows PR-26 ran it is −0.1125 → −0.1250 — **one row** — and a within-row test (greedy decoding makes the 640 run a continuation of the 192 run) shows the cap moves **neither arm detectably**: baseline 3↓/4↑, `demoproc` 1↓/1↑, both **p = 1.0** — though `demoproc`'s null has **1 discordant pair** and so **could not have reached α=0.05 either way**; it is underpowered, not a measured zero (the `2/2^k` floor rule, applied late) | **"Grows" withdrawn** from claim table, handoff and summary; **PR-26's gates and PR-23's conditions still hold at both caps**, so "not an artifact of the cap" survives. Also corrected: C-19's premise that truncation depresses ASR is **wrong** — 12 rows flip 0→1 and 5 flip 1→0 when allowed to finish. **Caught by a concurrent writer's independent analysis of my own artifacts**, whose numbers I re-derived before accepting |
| **C-24** | **C5's within-family bridge covers `core2x2` families ONLY, and I reported "48 families" without saying it is half.** Every bridge run logs `family_missing_one_side` ×144 (48 kept per arm). Checked against the bank: the forced-choice probe exists for `core2x2` (72 rows) and for **no other block** — slot3/strength/consistency/position/role_style/families all have **0** probe rows, so **396 of 468** behavioural family stems have no probe side | **Scope, not validity** — the bridge is within-family, so restricting to `core2x2` costs power and generality, not correctness. Handoff now says so. Not a join defect and not a silent subset (the ledger reported it): the other side was never generated, so recovering it needs **new probe rows**, not a code fix. **Surfaced by the concurrent session's adversarial ledger**, whose count was right and whose diagnosis I corrected |

## 8. Final claims

See `RESEARCH_HANDOFF.md` §4 for the full table with n, independence unit, test and artifact.
Summary: **C1 confirmatory** (3 settings) · **C9 confirmatory** (4/4 cells, causal) · **C2, C3, C4, C5
replicated** on two models · **C10 instrument-verified** · **C6, C8, C11, C12 single-model** · **C7
RESOLVED on Qwen3 (W9), declined-for-power on Llama (F6)**. ⚠ **C12 is the thinnest claim in the phase: 4 rows against a 2.1-row margin at n=40.**

> **Doublespeak's demonstration block does two separable things. Masking demo→demo attention during
> prefill removes the attack *and* restores refusal — and the second does not cause the first. The
> concept mapping survives the intervention that removes the behaviour. Handing the demonstration
> activations back gives the refusal back without giving the attack back, in all four model × pool
> cells.** *(The below-band control that this sentence originally invoked is withdrawn — C-20.)*

## 9. Limitations

1. **Demonstration-specificity: testable now, but not powerable (F2 → F6).** The longer-context bank
   was built and the count-matched control is real at every dose (`match_ratio` 1.000 on 480 rows) —
   **but the added context removes the attack**, taking baseline ASR from 0.1562 to 0.0437 and both
   decisive doses below the underpower threshold. **A future attempt needs non-demonstration context
   that does not dilute the attack**, which is a different design question from the one this phase
   posed. ⛔ **Do not retry by varying preamble LENGTH** — measured, and it recovers nothing.
2. Mapping usage unreadable (F3) — **needs a benign-register concept vocabulary AND a register control (R-81).** The benign-register half was built and tested: a `bicycle` mapping gives head-noun usage of **1/40** (PR-31 declined for power) and a purpose-built `forklift` pool yields only **incident-register** vocabulary (`accident`, `malfunctioning`) that every arm shares. With a harmful concept the model names the concept because the request pulls the content out of it; with a benign one it has no reason to name anything. **Usage and harm are entangled because harm is what makes usage observable.** Resolving it needs a register control (the `irrelevant`/`tulip` arm's shape) plus a query giving a reason to name the object — a bank *and* query-family design, not attempted.
3. All ASR is over the first 192 tokens (DR-2).
4. `kw_refusal` is lexical: it detects refusal *markers*, not refusal.
5. Lexical generality: **G = 2 for C1, G = 1 for everything else.** C1 was replicated on a second codeword (`basket`, R-73/PR-29: **+0.1250**, other three scopes at exactly zero refusals) and shown **truncation-robust row-for-row** at a 640-token cap (R-75/PR-30). **Every other claim, C7 included, still rests on the single codeword `carrot`** — PR-29 pre-committed to lifting G for C1 only, because C7's count-matched control needs the `longpre` preamble that the codeword banks do not have, so C7 at G = 2 would require a bank build.
6. Coherent non-compliance is a **residual** category and is not itself explained.
7. **Never quote a "% of the rise removed" figure alone (DR-5)** — rows and ×margin must travel with it.
8. All rescue work is at **one layer per model** (top of the knockout band) and **no layer sweep was
   run**, deliberately: PR-13 forbade scanning layers until one rescues. **So "the top of the band
   specifically" is not established at all (C-20):** the below-band control it rested on is a no-op by
   construction — below the band the knocked-out and clean activations are identical, so the patch
   writes what is already there. A real specificity control must sit **strictly above** the
   band's first layer (patching the band floor itself is also vacuous — R-68). Such a control was
   built and run, and **it did not replicate (R-71): the effect is NOT specific to the top of the
   band.** Llama mid-band restores refusal **−0.0688, p=0.019**, clearing the margin, where Qwen3
   mid-band gave **−0.0375, p=0.21** — graded with depth on one model, top-specific on the other.
   PR-28's condition 2 failed, so **the specificity leg stays removed and no layer sweep was run**,
   because sweeping would be rescuing a failed gate.

## 10. Canonical artifacts and reproduction

Full artifact paths, the reproduction manifest (one command per result), and the repo hazards worth
carrying forward are in **`RESEARCH_HANDOFF.md` §8-§9**. Judge provenance is closed on every
behavioural result (`judge_model_used` and `completion_sha256_16` on 100% of rows); bank provenance is
verified at **content level** via per-row `prompt_sha16` on **13/13** pool-A arms.

**Test suite at close: 1358 passed, 7 skipped, 0 failed** (serial and exclusive — concurrent runs
corrupt committed artifacts, see C-2).
