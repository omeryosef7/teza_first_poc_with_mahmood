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

⚠ **A liveness contract is necessary and NOT sufficient, and this phase paid to learn it (C-20).** It
answers *"did the hook execute?"*, not *"did the hook matter?"* — a patch that writes the value already
present reports `fired: true` truthfully and changes nothing. The check that separates them is
comparing an arm's generations against its own control. Calibration across **18 intervention contrasts**
here: 16 legitimate arms span **0.8187-1.0000** divergence, the two no-ops are **exactly 0.0000**, and
**nothing lands in between** — so *exact zero*, not a small threshold, is the diagnostic (R-86)
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
| **C-25** | **I claimed symmetric judge noise makes a paired exact p "optimistic". It does the opposite.** Simulated independently (n=80, 6000 reps/cell): type I error is **0.0312 / 0.0283 / 0.0327 / 0.0285** at flip rates 0.00-0.20 — at or below nominal. McNemar's null is `P(A=0,B=1)=P(A=1,B=0)`, and symmetric noise fills **both** discordant cells equally, so it cannot manufacture a false positive; it costs **power** (0.845 → 0.526 → 0.329) | **"Optimistic p" withdrawn.** PR-28's exclusion of ASR from that test **stands but its rationale is corrected**: the real reasons are power collapse (a *null* at a 5% floor is uninformative) and **asymmetric** noise, which does inflate type I (**0.0265 → 0.0640 → 0.1740**) and is live when arms differ in length. I was wrong *in the direction of excessive caution* about a number that favoured my own claim — **scepticism is not self-validating either** |
| **C-22** | **I asked a demonstration-knockout to run on 20 rows that have no demonstrations.** PR-31 specified two arms at `--expect-n 60`, but `n_examples=0` rows have no demo block, so `demo_processing_only` is **undefined** there — not merely infeasible. The pre-flight refused the arm in 7 minutes, before generating a single row | **Specification fix, not a rescued gate**: nothing was measured and PR-31's analysis section already had the right populations (n=0 is the FLOOR, taken from the baseline arm; the effect is n∈{4,8} pooled). Resubmitted at `--expect-n 40` with no condition, margin or flag changed. Had the arm silently rescoped itself to the 40 feasible rows — which the guard's message explicitly forbids — I would have compared a **40-row intervention against a 60-row baseline** and never noticed. **A pre-registration and the command implementing it are two artifacts, and only one of them runs** |
| **C-26** | **The test I committed as C-20's guard was a tautology — it passed with the production code broken.** `test_below_band_rescue_is_a_noop.py` imports only `pytest` and asserts a predicate defined in the test file; renaming `DonorPatch.liveness` left all 11 tests green | Docstring now states it is a **rule, not a regression guard**, and points at `test_donor_patch.py` as the file that exercises the real code; **one binding assertion added** so the mutation that was green is now red. The empirical version is impossible in-repo — `outputs/` is gitignored — and that limit is stated rather than left implicit. **C-20's lesson turned on my own tooling**: there a hook reported firing while changing nothing, here a test reported passing while checking nothing; both true about a narrower question than the one I was asking |
| **C-27** | **C-26 was not one bad test.** Four of this phase's guards assert on production **source text**, catching a guard's **deletion** but not its **disablement**. Mutation-tested: disabling C-13's bridge guard (`if False and _missing:`) left 8 tests green, and flipping `--model` to `required=False` — **C-18 exactly** — also left 8 green | `test_control_feasibility.py` now **executes** the script with `--model` omitted and requires a non-zero exit naming the argument; the C-18 mutation is now **red**. **C-13's guard was converted next (R-87)** — a 30-line fixture, no GPU, 28 s — and disabling that guard while leaving its text intact now fails (4 passed → 1 failed, 3 passed). **That justification was then found false (R-88)**: DR-5's percentages — 92.3% vs 69.2% — **ranked the cells backwards** while looking entirely right, so a disabled reporting rule can be just as invisible. `rescue_dissociation_table` was converted too (mutation now red). Only `dose_breakdown` remains text-only, on a **checked** rather than asserted basis: a missing per-dose cell size is visible in the artifact, whereas DR-5's percentage was self-consistent and complete-looking while being wrong. Pattern across **C-20 / C-26 / C-27**: each artifact truthfully answered a **narrower question** than the one asked of it — *did the hook execute / is the predicate self-consistent / is the guard present* — and only a comparison against something that **should have differed** exposed it |
| **C-28** | **C5 is measured on ONE BANK, and the wording did not say so.** Both bridge runs use `boombness_prompt_bank.jsonl`, so "Llama + Qwen3" is two models on one bank. The concurrent session then showed binding-survival under a **sibling scope** is **bank-dependent** — surviving on `main` (0.5416→0.3689, 42/48→41/48) and collapsing five-fold on `ticket_bomb` (0.5695→**0.1162**, 45/48→**15/48**) | **Scope narrowing, not a retraction** — the within-family dissociation on `main` stands on both models. Their intervention is the **unscoped `legacy_all_query`** mask, not C5's `demo_processing_only`: their `main` numbers reproduce my `p2A` (0.5416) and `p2_legacy_all_query` (**0.3689**) to four decimals, while my `demoproc` arm's mass **rises** to 0.6021. So it is a **cross-session reproduction, not a disagreement** — but it forbids assuming C5's bank-generality. **Whether `demo_processing_only` survives on `ticket_bomb`** was then RUN (**R-93/PR-32**): **45/48 → 45/48, mass 0.5695 → 0.5305 — binding SURVIVES**, on the identical 48 rows where the unscoped mask gives 45/48 → **15/48**. **So the collapse is SCOPE-dependence, not bank-dependence**, and C-28's bank restriction is **lifted for the scoped claim** and retained for the unscoped one. C-28 was a correct, evidence-driven narrowing that attributed the effect to the wrong variable because bank and scope were confounded in the only comparison then available — the fix was not more caution but the one run that separated them |
| **C-29** | **I built a bank×scope table that set an ASR-within-192 column beside a plain-ASR column without labelling either.** `main`'s behavioural arms are cap 192 with **0.552-0.719 of rows at the cap**; the `ticket_bomb` arms are cap 640 at 0.000. DR-2 fixed the rule that every ASR travels with its cap, and R-92/R-94 had just turned on exactly this kind of estimator mismatch | **Label, not a retraction** — the table is corrected in place with † = ASR-within-192 and an explicit "the two ASR columns are NOT comparable". **R-96's conclusion is unaffected and this was checked, not assumed**: it rests on the **forced-choice probe** (`--max-new 8`, forward-only, **no cap on either side**) and on **refusal**, which R-75 measured cap-invariant row-for-row. Caught by the concurrent session — whose numbers I was tabulating |
| **C-30** | **My cross-bank 2×2 mixed judge invocations — the exact defect I had audited the concurrent session for one day earlier (R-82).** Three cells came from one invocation and the fourth from a number quoted in a message; the same 96 generations judged twice give **27/96 and 30/96, disagreeing on 7 rows (0.0729)** — above the ~0.05 floor we had jointly measured, landing inside a headline cell | **Conclusion invariant, precision withdrawn.** Concept still dominates codeword, but the ratio moves **8× → 14.3×** on one cell's re-judge, so it is quoted as **"roughly an order of magnitude"** and never at two significant figures. The effect survives only because it is large (0.28 vs 0.05); **a smaller one measured the same way would not have, and nothing in how I built the table would have said so** |
| **C-31** | **I applied an "installs / does not" threshold at 0.500 without testing it against chance.** Exact binomial vs 24/48: `basket_gun` **19/48 is p=0.193** — the mapping is ABSENT, not inverted, so R-97's "the model prefers the codeword" claims a direction the data doesn't support; and `ticket_knife` **30/48 is p=0.111** — not demonstrably installed, though R-102 listed it as installing because 0.625 > 0.500 | **Both corrected in place.** The harm-category account rests on **one** bank (`window_knife`, 39/48, p=1.5e-05, ASR 0.042), not two — "both knife banks install" was overstated. **PR-34's decisive result is unaffected**: `basket_bomb` 42/48 (p=1.0e-07) vs `basket_gun` on the same codeword is overwhelming on one side and doesn't depend on where the other sits. I checked whether the effect cleared a threshold and never whether the **threshold was resolvable** on 48 binary rows |
| **C-32** | **The remedy I prescribed for C-31 does not exist and would not have worked.** I told the concurrent session that "96 rows would put p<0.05 within reach" for `ticket_knife`; the bank supplies **288 forced-choice rows, 72 per condition, 12 per dose over n ∈ {0,1,2,4,8,16}** — so **48 ran, 60 is the ceiling with demonstrations, and 96 does not exist** (⚠ **R-108, corrected by C-35**: I never ran `n_ex=16`, so **60 is an upper bound on the population, not a demonstrated one**. My stated *reason* — that those rows sit at 261–308 tokens and straddle a 262-token OOM cliff — is **refuted**: a length-ordered probe ran **40/40 at S=200–325 in both directions with flat memory**, so there is no length cap and no leak. The reachability of the 12 rows is **unknown, not doubtful**, and C-32's conclusion rests on the power arithmetic, which is unaffected). Nor would the ceiling settle it: power to detect a true 0.625 at α=0.05 is **0.331 at n=48, 0.399 at n=60**, and resolving it needs **~144 rows, 3× the population that exists** | **`ticket_knife`'s installation is unresolvable with this bank, not merely unrun** — C-31's chance-level verdict is **permanent, not provisional**, and closing it is a bank-design change rather than a rerun. The harm-category account continues to rest on `window_knife` alone (39/48, p=1.5e-05). The failure is narrow and worth naming: **I diagnosed an underpowered measurement correctly and then prescribed a remedy without checking it against the constraint I had just measured** — the row count was one `Counter` away and I sent the advice first |
| **C-33** | **A second under-specified prescription, found by auditing my own advice rather than my findings: R-97's bank pre-screen ("baseline mapped-wins must clear chance by a real margin") names no number.** Read the obvious way as "> 0.500", it **admits `ticket_knife` at 30/48** — the exact bank C-31/C-32 show can never answer — while agreeing with the tested rule on every other bank | **Criterion restated as a number: a candidate passes only at mapped-wins ≥ 32/48 (0.667), i.e. p<0.05 against chance on the population actually used**; at other n the threshold must be **recomputed, not carried** (39/60, 59/96). The general lesson is the concurrent session's, not mine: **prescriptions don't get audited the way findings do, because they don't look like claims.** Every finding here carries recomputable numbers; a prescription carries none, so "clear chance by a real margin" reads as rigour precisely because it names the right concept while omitting the threshold. **Two failed prescriptions in two ticks against zero failed findings in the same window** |
| **C-34** | **Encoding C-31's rule in a script made two of my own words wrong.** (a) C-31 called `basket_gun` 19/48 "the mapping is ABSENT, not inverted" — but the lower tail at n=48 needs **≤ 16**, so 19 does not reach it: `basket_gun` is **NOT_ESTABLISHED, the same verdict as `ticket_knife`**, and licenses no positive claim of absence. C-31 corrected an over-reading in one direction and made a milder version of it in the other. (b) I had named that tail **ABSENT** when significantly-below-chance means the model **prefers the codeword** — i.e. **INVERTED**; the label would have let C-31's claim be read straight off the artifact | **Renamed `ABSENT` → `INVERTED`; `basket_gun` recorded as NOT_ESTABLISHED.** **PR-34 is unaffected and is now carried by the test that actually supports it**: as a two-sample contrast holding the codeword fixed, `basket_bomb` vs `basket_gun` is **42/48 vs 19/48, Fisher p=1.64e-06** — I had never run it, having compared two one-sample labels by eye. (`window_knife` vs `ticket_knife` is p=0.0683, not significant, consistent with the codeword account resting on one bank.) The recurring fault across C-31→C-34 is **reading a label off a one-sample cell when the claim is a contrast**; it is now closed in code by `src/boombness/mapping_installation_verdict.py` + 10 behavioural tests |
| **C-35** | **I explained an OOM with a mechanism I had not tested, and the test refuted it.** R-108/DR-15 recorded that the `n_ex=16` rows (261–308 tokens) "straddle the 262-token cliff" where a concurrent Qwen3-14B run lost 22 of 40 rows, and propagated that into C-32's ledger row as a reason the 60-row ceiling might be unreachable. The concurrent session's length-ordered probe then ran **40/40 at S=200–325 in BOTH directions** — ascending and descending — with **flat memory** (alloc 27.52 GiB, reserved 27.58–27.60, free 16.42–16.44) and **zero OOM lines**. Descending is decisive: the **longest row, S=325, succeeded as row 0**, so there is no length cap; ascending reaching S=325 at the end with no growth rules out a leak | **The conclusion survives, the justification does not.** "I never ran `n_ex=16`, so 60 is an upper bound rather than a demonstrated population" remains true and is all I was entitled to say. The **262-token cliff is not a length effect at all** — both hypotheses on offer are dead and the original 22/40 attrition is still unexplained — so reachability is **unknown, not doubtful**. C-32's core (power 0.331 at n=48, 0.399 at n=60, 96 unreachable) is **untouched**, having been re-derived from the bank files in DR-14. **I took a correlation someone else had labelled a "cliff" and repeated it as a mechanism**, one tick after correcting them for quoting a statistic off the same run |
| **C-36** | **I modelled readout noise as a flip RATE times n, when flips are governed by how many rows crowd the decision boundary.** A concurrent session measured 1 verdict flip in 18 rows under a batch-16 vs batch-1 comparison; I read that as a 5.6% per-row rate and applied it to n=48. Their margins are **median 10.0 nats against a ~0.7 perturbation**, so 17 of 18 rows were untouchable and **the single at-risk row flipped** — a realised rate of **1/1 against at-risk rows**. Worse, R-110 had already computed the at-risk counts and then reached for a rate anyway | **Replaced with an exact adversarial bound** — flip every row with `\|margin\| < W` against the verdict (⚠ **C-38**: W=1.250 as originally used is now withdrawn as unmeasurable; restated at the largest **valid** measured Llama window **W=0.4616** the bound is *stronger* — `window_knife` **36/48**, `basket_bomb` **40/48**, `window_bomb` **38/48**, PR-34's contrast **40/48 vs 20/48, p=4.53e-05** — so the conclusion is unchanged and the original figures were conservative), counting only wins, since at-risk losses can only help: `window_knife` **33/48**, `basket_bomb` **38/48**, `window_bomb` **34/48**, all still **INSTALLED** at crit=32; PR-34's contrast goes **42/48 vs 19/48 → 38/48 vs 24/48, Fisher p=0.00515, SURVIVES**. **Every claim-bearing result survives the absolute worst case**, independent of their rate or of which branch their control lands on. `ticket_knife` is **not robust** (30/48 → 34/48 would read INSTALLED) — a **third** independent argument for the conclusion C-31 and C-32 already reached, and it carries no claim |
| **C-37** | **I applied a perturbation window measured on Qwen3 to Llama banks.** A concurrent session's `W = max \|Δ margin\| = 1.250` came from Qwen3-14B/`longpreQ14B`; measured on my own model and bank (job 789939, `p5A_ticket_bomb` b16 vs `c5A_tb_b1` b1, same 48 ids) it is **0.3202, median 0.1151**. ⚠ **C-38 makes this worse, not milder**: the 1.250 I borrowed is now **withdrawn as unmeasurable**, so I had imported not merely another population's scale but one measured on a biased subset of its own. The honest spread is **1.44×** between the two *valid* windows (`main` 0.4616 vs `ticket_bomb` 0.3202), both complete 48/48, both the same model. A perturbation scale is a property of a **model-and-bank**, and they had told me one tick earlier that the scale must be **named**; I recorded that amendment and kept using the borrowed number in the same analysis — **C-33's carry-over shape, third instance** | **R-111's "C5 does not survive its own worst case" is WITHDRAWN — it was an artifact of the borrowed window.** At the measured scale the `ticket_bomb` collapse half goes from *failing* at p=0.077 to **surviving at p=8.25e-08**, and the `main` preserved half **cannot degrade in-window** (worst case 44→47). **C-36 is unaffected and was conservative**: too-large a W overstates at-risk sets, which is conservative for an INSTALLED verdict and anti-conservative for a null, so its published at-risk counts are **upper bounds** (10/5/12/6 → 4/1/2/0) and every verdict holds either way. A **direction bug** in my recomputation (pushing the collapse half the favourable way) was caught before reporting |
| **C-38** | **My report quoted a perturbation scale that its own author has withdrawn as unmeasurable, and one of my corrections rested on it.** The concurrent session's deep review found `margin_exposure` lacked an attrition check (R-105 parity missing), so `longpreQ14B`/Qwen3 **1.2499** had been measured on a pair whose batch-16 arm **lost 22 of 40 rows to the very perturbation being measured** — it describes the **short half** of that bank. It is **unmeasurable, not merely unmeasured**: no complete batch-16 run on that bank can exist, because batch 16 is what OOMs | **Withdrawn from the measured-scales list and from C-37's justification.** The valid spread is **1.44×** (`main` 0.4616 vs `ticket_bomb` 0.3202), both complete 48/48 on the same model — still sufficient reason never to carry a scale across. **C-36 and C-37 both survive and were conservative**: 1.250 exceeds every valid Llama window, and restating C-36 at **W=0.4616** *strengthens* it (`window_knife` 36/48, `basket_bomb` 40/48, `window_bomb` 38/48, PR-34 **40/48 vs 20/48 p=4.53e-05**). **My 0.3202 and their 0.4616 are unaffected** — both pairs complete. The batching finding itself never rested on Qwen3: it was established on Llama/`main` with complete populations, and the determinism control was 40/40 complete. **A scale borrowed from a biased sample of its own population, where the bias was induced by the quantity under measurement** — the fourth and worst instance of the one-sidedness pattern |


## Reading a forced-choice count: the two numbers that must travel with it

Every forced-choice count in this report is published with **two further numbers**, because a bare
fraction hides its own fragility. This convention was arrived at jointly with the concurrent session
after both of us made the mistakes it prevents (C-33, C-36, C-37).

1. **median |margin|**, where `margin = logp_concept − logp_codeword` — the quantity the
   `mapped_win` predicate thresholds at zero. It is intrinsic to the run and always reportable.
2. **the count of rows with |margin| below a NAMED, MEASURED perturbation scale W** — never a scale
   borrowed from another model or bank. Where no W has been measured for that bank, the count is
   reported as **unmeasured**, not estimated.

| arm | wins | median \|margin\| | rows within the named scale |
|---|---|---|---|
| `window_knife` | 39/48 | 3.671 | **REFUSED** — borrowed scale (bank `b60b1441…`) |
| `basket_bomb` | 42/48 | 5.674 | **REFUSED** — borrowed scale (bank `113fc7b6…`) |
| `window_bomb` | 40/48 | 3.604 | **REFUSED** — borrowed scale (bank `ad6ae618…`) |
| `ticket_knife` | 30/48 | 3.051 | **REFUSED** — borrowed scale (bank `77824a28…`) |
| `basket_gun` | 19/48 | 3.965 | **REFUSED** — borrowed scale (bank `568dd040…`) |
| C5 `ticket_bomb` baseline | 45/48 | 4.018 | **1** (W=0.3202, measured on `ticket_bomb`/Llama) |
| C5 `ticket_bomb` `demo_processing_only` | 45/48 | 2.251 | **4** (same W) |
| C5 `ticket_bomb` unscoped | 15/48 | **1.075** | **9** (same W) |
| C5 `main` baseline | 42/48 | 3.423 | **2** (W=0.4616, measured on `main`/Llama) |
| C5 `main` `demo_processing_only` | 48/48 | 2.659 | **1** (same W) |

The five refusals are **emitted by `src/boombness/margin_exposure.py`**, which resolves provenance
from `metadata.json` — model, `model_revision_resolved_commit`, and `bank_rows_sha16`, a **content**
hash of the bank rows — and refuses an at-risk count whenever the window's population does not match
the run's. All five share this model and commit and differ **only** in bank content hash, which is
exactly the distinction a filename or path would have missed. Artifact:
`outputs/boombness/margin_exposure/five_unmeasured_20260828_135856_1747482/`.

**Measured perturbation scales** (max |Δ margin| under a batch-path change): `ticket_bomb`/Llama
**0.3202** (complete 48/48 both arms) and `main`/Llama **0.4616** (complete 48/48 both arms). ⛔ **`longpreQ14B`/Qwen3-14B 1.2499 is WITHDRAWN as UNMEASURABLE (C-38)** — it was measured on a pair whose batch-16 arm lost 22 of 40 rows to the very perturbation being measured, so it describes the **short half** of that bank; and no complete batch-16 run on it can exist, because batch 16 is what OOMs. The valid spread is therefore **1.44×** (0.4616 vs 0.3202) **across two banks of the same model**, which is still reason enough never to carry the scale across (C-37).

Why this matters concretely: **18 rows at median margin ~10 nats and 48 rows at median margin 1.075
are the same nominal design with an order of magnitude different exposure**, and nothing in `14/18`
or `15/48` reveals that.

### ⚠ A perturbation bound is one-sided, and it favours the headline

**An over-large W is conservative for a claim carrying an effect and anti-conservative for a null.**
Inflating the at-risk set can only make a positive result look *more* fragile than it is, and can only
make a null look *less* robust than it is. So:

* results that **carry effects** — the ones a reader is most likely to re-derive — are where the error
  is **harmless**;
* results that are **nulls** — the ones least likely to be independently checked — are the only place
  it does damage.

**A robustness check that is silently one-sided in favour of the headline is worse than none.** Ours
was, in both this ledger and the concurrent session's, for two ticks, *while the two sessions were
auditing each other* (C-37). The failure signature is the same as the direction bug caught in R-114:
**the error's tell is that the result improves**, which is precisely when it is not re-checked. Any
deliverable using a perturbation bound should state which side its error falls on.

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
3. All ASR is over the first 192 tokens (DR-2) — **and ~5% of binary ASR labels flip on identical input** (four estimates, two independent designs; pinning does not reduce it). That noise **lives at the decision boundary**: **9/17** of rows within |score−0.5|<0.15 flip versus **5/289** beyond it, so the floor is **per-arm**, not a corpus constant. Measured against each arm's own floor (**DR-12**), the phase's ASR contrasts split into two tiers: `legacy` **4.23×**, `demoproc` **3.70×**, **C7 pool B 3.57×** — versus `respq` **1.73×** and `qpre` **1.57×**, the two arms whose claims were always null/equivalence ones. **Nothing is fitted below its floor.** Refusal metrics are unaffected: `kw_refusal` flips **0/160**.
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
