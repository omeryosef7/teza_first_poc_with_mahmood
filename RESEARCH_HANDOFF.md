# RESEARCH HANDOFF — Demonstration Retrieval → Behavioral Causality phase

**Branch:** `behavioral-causality-sprint` · **HEAD at writing:** `423fcc61`+ (see git log; R-29 added 2026-08-25 18:35)
**Live log (authoritative, chronological):** `external_md/DEMONSTRATION_RETRIEVAL_BEHAVIORAL_CAUSALITY_NEXT_PHASE_PLAN_AND_PROGRESS.md`
**Date:** 2026-08-25

This file is §19-C/D/E. It is written to be read with **no session context**. Where a claim and an
earlier document disagree, **this file and the live log win** — several headline framings from earlier
in this phase were withdrawn, and they are listed below precisely so they are not revived.

---

## 1. The one-paragraph scientific truth

Masking attention to the demonstration block removes the doublespeak attack. Decomposing that mask by
**which query rows** it applies to shows the removal is **not localised to response-time retrieval**:
four scopes (`legacy_all_query`, `demo_processing_only`, `response_query_only`, `query_prefill_only`)
all remove attack, and at matched dose they remove **statistically indistinguishable** amounts. **One
scope is different in kind, not degree:** `demo_processing_only` — masking demo→demo attention during
prefill — is the **only** scope on **either** model that **restores refusal** (Llama refusal
0.0563 → 0.2188; Qwen3 0.0125 → 0.1437; every other arm at or **below** baseline). That restoration
**does not explain the attack removal** — at matched dose, arms restoring zero refusal remove exactly
as much attack, and on Qwen3 more. The concept binding **survives** the intervention on both models. ⚠ **CONTRADICTED ON HELD-OUT
BANKS by this sprint (`RBD-R-025`/`R-032`): binding FALLS −0.2125 (Llama) and −0.8250 (Qwen3) under
the same `demo_processing_only` scope.** The preservation below is scoped to `main`/`ticket_bomb`,
`core2x2`, 48 families; the sprint tested 20 held-out domains × 80 families on two new lexical pairs
and did not reproduce it. **Where this file disagrees with itself, the held-out result wins.**
**Net: the intervention has two separable effects — it removes the attack, and it restores refusal —
and the second is not the mechanism of the first.**

## 2. Strongest results

**Three, and C7 was the phase's longest-running open question.**

**(0) Attack removal is DEMONSTRATION-SPECIFIC (C7, R-58 + R-62).** On Qwen3, masking the
demonstration positions removes **5 of 5** attacks at `n_examples`=4 and **5 of 7** at n=8, while
**three independent count-matched masks of the same size drawn from elsewhere** remove **1, 2, 2**
and **2, −2, −1** — all inside the pre-registered margin. Separation **2.0×** and **3.2×** the
arm-vs-arm margin. **Replicated on an independent pool** (R-62, PR-25): **4 of 4** and **5 of 6**,
controls **+1, +1, +1** and **0, −1, −2**, separation **3.0×** and **1.8×**. **The effect is about
which positions they are, not how many.**

⚠ Single-model: Llama's version was **declined for power** (R-52), never refuted.

✅ **Truncation-robust (R-64, PR-26).** The numbers above are ASRs over the first **192** generated
tokens, on an arm that terminated on only 0.325/0.300 of its rows versus 0.519–0.606 for its controls
(C-19). Re-generating the contrast at a **640-token cap**, where **every** arm stops on length **0.000**
of the time and the longest completion is 634 tokens, the effect **survives at the same size** (the cap moves neither arm detectably — C-23): `demoproc`
removes **3 of 4** attacks at n=4 (−0.0750) and **7 of 7** at n=8 (**−0.1750**, up from −0.1250), while
the count-matched control moves **+1** and **+0** — separation **2.4×** and **4.2×**. The truncation
hypothesis predicted the effect would shrink once completions could finish; it did the opposite.
⚠ The untruncated n=4 cell is the thinnest in the claim, **−3 rows against a 2.08-row margin (1.4×)**,
and the 640-token result rests on **one** count-matched control rather than three.

**(a) `demo_processing_only` uniquely restores refusal**, across two model families and two
demonstration pools, measured with a deterministic instrument. Refusal here is `judge_boombness.kw_refusal` — a keyword detector, **not
the LLM judge** — so it carries none of the judge's measured session drift (78/96 binary agreement
across sessions).

| model | baseline refusal | `demoproc` | rise | killed-by-refusal | other three arms |
|---|---|---|---|---|---|
| Llama-3.1-8B-Instruct | 0.0563 | **0.2188** | **+0.1625** | **14/25 (56%)** | **0/24, 0/24, 0/18** |
| Qwen3-14B | 0.0125 | **0.1437** | **+0.1312** | **8/20 (40%)** | **0/19, 0/20, 0/15** |

**Eight arm×model cells on pool A; exactly one restores any refusal at all.** Pre-registered in
**PR-6** before the Qwen3 data was read (3/3 conditions held), and **replicated on an independent
demonstration pool** in **PR-12** (2/2 conditions held; Llama pool B rise **+0.1938**, baseline
refusal 0.0063 — R-29). ⚠ On pool B `legacy` and `respq` each show **1** killed-by-refusal row rather
than 0; both remain inside the margin, but "exactly zero in every cell" is no longer accurate.

**(b) A per-position activation patch separates the two effects causally (C9).** Handing back the
clean demonstration activations at the top of the knockout band removes **12-18 refusal rows** in **all four** model × pool cells, every one clearing the 8.3-row margin (1.44-2.16x) **while leaving the attack removal intact on Llama** (Outcome C, recovers 16.7%). The
**below-band control at the same positions moves refusal by exactly 0.0000 in all four cells**, and the
identity control reproduces its own arm **8/8 byte-identical**. **This converts C2 from a
correlational dissociation into a causal one.**

## 3. ⛔ Retracted / withdrawn — DO NOT REVIVE

| # | Claim that must not be repeated | Why | Ref |
|---|---|---|---|
| 1 | *"`demo_processing_only` works BY restoring refusal"* | At matched dose, zero-refusal arms remove the same attack (Llama n=4: **−0.1750 / −0.1750 / −0.1750**, gaps 0.0000). On Qwen3 n=8 the refusal-restoring arm removes **less** (−0.1500 vs −0.2000). | **C-12 / R-23** |
| 2 | *"`response_query_only` is a weak partial (46% of legacy)"* — Outcome B | Does not replicate at k=10: respq is **85%** of legacy, gap **0.0188**, passing the same pre-registered margin it failed at k=6. | **R-19** |
| 3 | Any **ranking** of the three effective arms by ASR | Gaps demoproc-vs-legacy **0.0250** and legacy-vs-respq **0.0188** are inside the pre-registered **0.0417** margin. Ranking below the instrument's reproducibility is the error the margin exists to prevent. | **C-11** |
| 4 | *"The mapping stops being used when the attack dies"* | Concept-term usage is **confounded with the outcome** — killed rows (0-11%) match baseline **non-jailbroken** rows (6%/10%). In this bank "mentions bomb" ≈ "is a jailbreak". | **R-27** |
| 5 | Dose-response as a **cross-model** mechanism | Confirmed on Llama (+0.0000 → +0.3500, monotone, 6.7× margin) but **refuted on Qwen3** by the pre-registered endpoint rule (+0.0250, within margin). | **R-22** |
| 6 | *"The rescue restores the attack on Qwen3"* | Failed PR-15's confirmatory test on an independent pool: **+0.0625 (pool A) vs +0.0437 (pool B)**, threshold 0.0521. Never promoted to a claim — recorded here so the pool-A number is not revived on its own. | **R-37** |
| 7 | `d_surface` as an attack objective | Closed earlier in the sprint; not reopened. Gate in §7 remains **BLOCKED**. | prior phase |

## 4. Paper-level claim table (§19-D)

Status key: **R** replicated (2 models) · **S** single-model · **N** evaluated negative · **U** unresolved/untestable.

| # | Claim | Model(s) | Population | n | Independence unit | Effect | Test / margin | Intervention | Control | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 | `demo_processing_only` restores refusal; no other scope does | Llama + Qwen3, **2 independent pools, 2 CODEWORDS** (R-73: `basket` **+0.1250**, other three scopes at **exactly zero** refusals; **truncation-robust — R-75**: re-run at a 640-token cap with 0.000 truncation gives **the identical +0.1250 on the SAME 14 rows** while 81/96 completions changed) | d10 behavioural, natural_doublespeak | 160 × 3 settings | prompt (rate), domain (sign) | **+0.1625** (Llama/A), **+0.1312** (Qwen3/A), **+0.1938** (Llama/B) | vs `MARGIN_VS_BASELINE` 0.0521; PR-6 3/3 **and** PR-12 2/2 | attn knockout, demo→demo prefill | 3 other scopes, all within margin | **CONFIRMATORY** **⬆ CAP-RELEASE CONFIRMED ON LLAMA (R-141): `g3A640`/`g3dp640`, `basket_bomb`, 640-cap, `frac_stop_length` 0.000 both arms, refusal 2 → 14 (+12) with ASR 32 → 11. And the T1/T2 decomposition gives T1 between −3.1 and +2.7 across all C1 sessions, usually NEGATIVE — truncation was MASKING the restoration, so the 192-cap numbers are conservative.** **⚠ BANK-SPECIFIC NULL (R-146): absent on Qwen3 + `longpreQ14*` in 3/3 sessions (`q15j` +0, `q16j` −1, `p26j` −1) with FULL headroom — baseline refusal 0-9 of 80-160 everywhere, so this is not a floor. Both Qwen3 sessions on other banks show it (`q1j` +14, `q4bj` +21). Present in 8/13 sessions overall.** |
| C2 | Refusal restoration is **not** the route to attack removal — **corroborated on a 3rd bank (R-95)**: non-refusal share of down-flips is **80% / 76% / 69%** (Llama d10 / Qwen3 / `ticket_bomb`). ⚠ **A minority everywhere and never zero** — refusal is a real component of how the model declines, not an absent one | Llama + Qwen3 | same | 160/model | prompt, dose-matched **and causally, both models** | Llama n=4 gaps **0.0000**; Qwen3 n=8 refusal arm **worse**; **R-35/36/37/38 — a COMPLETE 2x2 (model family x demonstration pool): refusal rows removed 18 / 17 / 12 / 18 against an 8.3-row margin (2.16x / 2.04x / 1.44x / 2.16x), while the below-band control moves it by exactly 0 rows in all four. As percentages of the rise: 69.2 / 81.0 / 92.3 / 58.1% — but those are INVERTED relative to the evidence (DR-5), because a near-zero clean baseline inflates the ratio** | arm-vs-arm 0.0417 | same | zero-refusal arms; below-band L5 patch | **R + CAUSAL** | **⛔ BANK-SCOPED (C-82): the non-refusal share of down-flips runs 44%-100% across 13 bank/model pairs, and the two quoted (80.0%, 76.5%) are the `base` pairs, mid-range. `correlation(share, Δrefusal) = −0.877`. On `p4bj`/`d10` the share is **44.0%** — 56% of attack removal travels WITH a refusal, against the set's largest restoration (+26) — so C2 is CONTRADICTED on `d10`, the family most of the sprint runs on. It holds strongly where refusal never moves (`longpreQ14*`: 11 and 16 attacks die at Δrefusal −1 and 0).**
| C3 | The four scopes remove indistinguishable amounts of attack | Llama + Qwen3 | same | 160/model | prompt | all pairwise gaps ≤ 0.0417 except marginal `qpre` pairs | arm-vs-arm 0.0417 | same | each other | **R** |
| C4 | Attack removal proceeds by **coherent non-compliance**, not degeneration | Llama + Qwen3 | killed attacks | 165 across 8 cells | killed row | **0** degenerate rows; `frac_scorable` 1.000 | `coherence_gate` thresholds, mutation-verified | same | positive/negative detector controls | **R** |
| C5 | ✅ **BATCH CONFOUND MEASURED AND CLOSED (R-114).** The two arms did run different code paths (baseline batch 16, knockout batch 1, `score_behavior.py:1735`) and batching is **not** numerically inert. Both legs now have matched-batch reruns: `ticket_bomb` **45/48 → 45/48, 0 flips** (job 789939, `c5A_tb_b1_20260828_125009_2294147`, pre-registration held) and `main` **42/48 → 42/48, 0 flips, per-row vector identical** (their 789942), so the main-leg **+6, p=0.0265** stands as computed. Measured window on Llama/`ticket_bomb` is **max \|Δ margin\| = 0.3202** (median 0.1151) — **C-37: the 1.250 I first used was a Qwen3 number, and C-38: that number is now withdrawn as unmeasurable, having been measured on a pair whose batch-16 arm lost 22 of 40 rows to the perturbation itself**, and at the measured scale the collapse half survives adversarially at **p=8.25e-08** where the borrowed one said it failed. ⚠ This **removes a confound and creates no power**: the preserved half is still a **null** claim. Original claim: The baseline reads at batch 16 and every knockout arm is pinned to batch 1 by C-8 (`score_behavior.py:1735`), and batching is **not** numerically inert: a concurrent session measured **0/18 rows bit-identical** across b16/b1 with one verdict flip, and my `q8D` vs `qbD` control (both batch 1, different runs) is **bit-identical 40/40**, so the difference is **batching, i.e. a systematic bias sitting exactly where the intervention sits**, not noise. C5 **fails** the adversarial bound that C-36's verdicts passed (collapse half 45v15 → worst case 42v34, **p=0.077**; the unscoped arm's median margin is 1.075 with 32/48 rows at-risk), which makes the bound uninformative rather than disconfirming — **the magnitude must be measured, and a batch-1 baseline rerun is pre-registered** — **✅ EXPIRED (R-167): it RAN. Job 789939 / R-114 measured the batch confound on `ticket_bomb` to ZERO and both pre-registered legs held, so C5 is closed by measurement rather than awaiting one**. Nothing observed contradicts C5. Original claim (⚠ **CONTRADICTED ON HELD-OUT BANKS — `RBD-R-025`/`R-032`; the "LIFTED" restriction is REINSTATED: preservation is scoped to `main`/`ticket_bomb`/`core2x2`**): Concept binding **survives** the intervention — **`demo_processing_only` scope; bank restriction LIFTED (R-93)**: preserved on `main` (0.5416→0.6021) **and** `ticket_bomb` (45/48→45/48, mass 0.5534→0.5201 true-median) where the **unscoped** mask collapses it (45/48→**15/48**); **independently replicated by a second session, exact agreement on all counts and masses (R-94)**. The scope, not the bank, is what destroys binding | Llama (2 banks) + Qwen3 (1 bank) | forced-choice probe | 48 families/model — **`core2x2` ONLY (C-24)**: the probe was never generated for the other six blocks, so 396 of 468 behavioural family stems have no probe side and cannot join. Scope, not validity | family (within-family 2×2) | Llama 0/48 binding lost; Qwen3 0/10 killed lost | McNemar / contingency | same | `legacy` loses 28/48 (Qwen3) | **R** |
| C6 | Refusal restoration scales with demonstration count | **Llama only** | d10, by `n_examples` | 40/cell | prompt | +0.0000 → +0.3500, monotone. **⬆ CAP-RELEASE REPLICATION on a 2nd bank (R-156)**: `g3`, Llama/`basket_bomb`, 640, 0.000 truncation, 24/cell → **+0.0000 → +0.3333**, monotone, exact (`kw_refusal` has zero judge variance). **⚠ SCOPE: measured only over n ≤ 8**, and the monotonicity is `0 = 0 < 4 < 8` — two ties then two rises, equally consistent with a threshold at n=4. Their Phase-6 ladder finds the ASR analogue **non-monotonic, peaking at 8-12 and falling at 16**; refusal restoration has never been measured at 12 or 16, so this is not a monotone law in n | endpoint vs 0.0521, 6.7× | same | `legacy`/`respq` flat at ≤0 | **S** |
| **C7** | **Attack removal is DEMONSTRATION-SPECIFIC** | **Qwen3-14B** (Llama **declined for power**, not refuted — R-52) | `longpreQ14`, `n_examples` **4 and 8** | 40/dose; **5 and 7** baseline attacks | prompt, **3 independent draws** | `demoproc` removes **5/5** and **5/7** attacks (−0.1250 each); controls remove **1,2,2** and **2,−2,−1**, all within ±0.0521 — ⚠ but pool A's `d2`/`d3` were judged in a **separate invocation** from their baseline and their 1-2 row readings sit at the ~2-row judge floor (**R-82**), so the pool B replication carries that leg. **Quantified (R-83)**: against a per-arm judge floor those two cells are **0.00× and 0.38×** the paired noise SD, while pool B's effect is **3.6×** (−9 rows vs SD 2.52); separation **2.0×** and **3.2×**. **Pool B (R-62): −4/4 and −5/6, controls +1,+1,+1 and 0,−1,−2, separation 3.0× and 1.8×**. **Untruncated at a 640-token cap (R-64): −3/4 and −7/7, control +1 and +0, separation 2.4× and 4.2×** | PR-23, committed before the bank existed; all three conditions at **both** doses | `demo_processing_only` 7-17 | **strict count-matched non-demo mask, `match_ratio` 1.000 on all 480 control rows**, 3/3 distinct draws | **S → RESOLVED** (single-model; **replicated on a 2nd pool** R-62; **truncation-robust** R-64) |
| C8 | `query_prefill_only` is a measured null | Llama | d10 | 160 | domain | −0.0250, p=0.6875 | sign test, floor 0.0312 | attn knockout, query prefill rows | other scopes | **S** (negative) |
| **C9** | **Handing back the clean demonstration activations at the top of the knockout band gives back the REFUSAL and not the ATTACK** | Llama + Qwen3, **2 pools** | d10 / d10-poolB behavioural | 160 × 4 cells | prompt | refusal rows removed **18 / 17 / 12 / 18** vs an **8.3-row margin** (1.44-2.16x); as % of rise 58-92%, **inverted relative to the evidence — see DR-5**. ASR: Llama Outcome **C** (null, recovers 16.7%) | vs `MARGIN_VS_BASELINE` 0.0521; PR-13 / PR-14 / PR-16, each committed before its data | per-position `DonorPatch` at L14 (Llama) / L17 (Qwen3), donor = clean forward, same `templated_r` | ~~below-band L5 patch: refusal EXACTLY 0.0000 in all four cells~~ **WITHDRAWN (C-20): that arm is byte-identical to knockout-only on 160/160 rows — a no-op by construction, not a control. C9's specificity leg is unsupported; its primary effect stands**; identity control (`--rescue-donor self`) 8/8 byte-identical; **⚠ TRUNCATION-EXPOSED (C-60): every rescue arm ran at the 192-token cap and the rescue arm is MORE truncated than its knockout-only comparator — +0.087 / +0.099 (Llama), +0.025 / +0.050 (Qwen3). The differential is far below the 0.300 that C7's cap release collapsed to 0.000, and refusals surface early, but C7 earned its status by RELEASING the cap and C9 has not. A 640-cap rerun of both rescue arms plus comparator is the remedy; queued, not launched.** — **✅ EXPIRED (R-167): it RAN.** PR-36 delivered it (Llama −18 at 0.0000 truncation, R-143) and PR-38 supplied the powered Qwen3 arm, passing all three gates (R-154). Nothing here is outstanding. | **✅ CONFIRMATORY (4/4) + CAP-RELEASE LEG (R-143)** — at 640 with **0.0000** truncation on both arms, judged in one invocation: refusal **35 → 17 = −18 rows** against an 8.3-row margin (**2.2×**), **ASR unchanged 5 vs 5**, all three PR-36 gates pass. **C-64's "below margin" is RETRACTED (C-67)**: its T1 treated truncated rows as cap-suppressed refusals, but releasing the cap converted **zero** of the 116 newly-finishing L5 rows (17→17, 35→35), so `stop_reason=length` is a *marker* of non-refusal, not a cause. Single-session contrast, not exposed to cross-session judge drift. **⚠ C-71: refusal ICC across domains is 0.3260-0.4267 on these arms, so n_eff ≈ 22-27, NOT 160 — any interval on a refusal outcome here must use the effective n. The −18 rests on a paired within-session contrast and an 8.3-row margin rather than an n=160 approximation, so it stands; the caveat binds future intervals.** **⛔ HEADLINE SPECIFICITY IS LLAMA-ONLY (C-68): "and not the ATTACK" fails on Qwen3.** Ladder on `q6b` (160 rows): clean 2 refused / 22 ASR → knockout 15 / 7 → rescue **3 / 14**, so the rescue undoes the knockout on BOTH axes. ΔASR = **+9, +13, +10** across `q6b`@192, `q7`@192 and `q6`@640, against Llama's **+0**. Distinct from the below-band control C-20 withdrew. **Primary refusal effect stands on both models; the selectivity clause is scoped to Llama.** **PR-38 (R-154) supplies the powered arm and PASSES all three gates** — `q7`/`d10`, cap 640, 0.0000 truncation both arms, comparator baseline attacks **4** (at the threshold): Δrefusal **−17**, ΔASR **+14**, matching its pre-registered prediction. Across four independent Qwen3 measurements the rescue restores attack by **+9, +13, +10, +14** against Llama's **+0**, so the Llama-only scoping is established rather than observed. ⚠ refusal ICC 0.065-0.148 on these arms → n_eff ≈ 50-81, not 160 (C-71). |
| **C13** | **Neutral context that touches neither the demonstrations nor the query suppresses the doublespeak attack — LLAMA-SPECIFIC** | Llama only (**Qwen3 tested and NEGATIVE**: 21/160 → 23/160, +2 rows, powered, 0 drift — R-54; **the model-specificity is now tested as an INTERACTION rather than inferred from two one-sample results — R-104: dd = −0.1437, z = −2.83, p = 0.0047 (longpre12) and dd = −0.1375, z = −2.69, p = 0.0072 (longpre10); the unpaired variance is used although the within-model comparisons are paired, so both are conservative; **DR-15 re-derived the interaction by permutation (20k relabelings, seed 20260828) and gets p = 0.0064 vs the z-test's 0.0047 — same conclusion, and the permutation is the figure to quote**) | d10 vs longpre12 vs longpre10 baselines, same judging window | 160 each | prompt | **27/160 → 6/160 and 7/160**, i.e. **−21 and −20 rows** vs an 8.3-row margin (~2.5×) | PR-21, committed before the re-judge; cross-session drift measured at **2-4 rows** on identical completions | ~10 neutral sentences prepended **outside `demo_block`** | banks verified to differ **only** by the preamble (200/200 rows, `tests/test_preamble_is_the_only_difference.py`); **⛔ TRUNCATION-CONFOUNDED (C-61): the preamble arms are 0.912/0.919 truncated against a 0.581 baseline — Δ +0.331/+0.337, LARGER than the 0.300 that forced C7's cap release. Median completion RISES 794 → 920/928 chars, so the arm makes the model more discursive and it hits the 192-token cap more; 'suppresses the attack' and 'rambles until it runs out of budget' predict the same −21 rows and this design cannot separate them. The interaction (R-104/DR-15) inherits it: the truncation differential is itself model-dependent, +0.331 Llama vs +0.175 Qwen3.** | **ASR LEG RESOLVED — the 640-cap rerun RAN (R-178/PR-39): REINSTATED AT ROW LEVEL, NOT ESTABLISHED AT CLUSTER LEVEL.** At a released cap, `pre12` **11/160 = 0.0688** and `pre10` **12/160 = 0.0750** against baseline **23/160 = 0.1437** — deltas **−0.0750** and **−0.0687**, **12 and 11 rows**, **1.45× and 1.33×** the 0.0521 margin, so the pre-registered criterion is met. ⚠ **On DOMAIN means — PR-1's independence unit — the two arms are NOT comparable negatives (C-95): `pre12`'s test was CAPABLE (k=7, attainable floor 0.0156) and returned p = 0.125 on 6/7 informative domains — a genuine informative negative; `pre10`'s test is UNINFORMATIVE BY CONSTRUCTION (k=5, floor 0.0625 > 0.05, so no outcome could have reached significance) and must not be quoted as a negative.** Truncation is ruled out as the cause (`frac_stop_length` 0.5813→0.0000 baseline, 0.9125→0.0187 and 0.9187→0.0187 arms; baseline ASR moves only −0.0250 between caps) — **but the effect HALVED on cap release** (−0.1313 → −0.0750; −0.1250 → −0.0687), so C-61's mechanism contributed materially without accounting for it. *(prior status: SUSPENDED; C-66 had downgraded C-61's WITHDRAWN)* — C-61's mechanism is retracted: P(ASR\|truncated) 0.0981 vs 0.0925 finished over 76 runs, so a cut-off completion does NOT score low, and C13's drop holds WITHIN each stratum (`pre12` 0.041 vs baseline 0.204 truncated; 0.000 vs 0.119 finished). Not reinstated: truncation is a post-treatment collider and the finished cells are 14/13 rows. Interaction still scoped to the 192-cap population |
| C12 | **The demo/query contrast is position IDENTITY, not position count — but demo-patch magnitude also scales with count** | Llama | d10, `n_examples`=8 | **40** | prompt | at **24 positions each**: demo removes **4** refusal rows and **0.0000** ASR; query removes **13** and **+0.0500** ASR. 24 of ~114 demo positions = **36.4%** of the full effect | PR-18; ⚠ margin is **2.1 rows** at n=40; **⛔ C-70: the ASR half is AT THE FLOOR — the demo-vs-query ASR contrast is 2 rows against a measured 1.9-row floor (1.1 SD), so "demo 0.0000 vs query +0.0500" must NOT be quoted as showing the query patch restores attack and the demo patch does not. The refusal contrast (4 vs 13) passes through `kw_refusal`, has ZERO judge variance, and is what the claim stands on.** | size-matched seeded `DonorPatch` draw | ~~below-band L5, exactly inert (15→15)~~ **WITHDRAWN (C-20): byte-identical to knockout-only on 40/40 rows — vacuous, not inert** | **S** (single-model, thin) |
| C11 | **The attack damage is reachable from the QUERY span but not from the demonstration positions — and the query patch is NOT selective** | Llama (**refusal half + dissociation REPLICATE on Qwen3, R-70: −0.09375 (−15/160), 71.4% of the rise, dissociation 0.0875; ASR half DECLINES for power, −0.0062**) | d10 behavioural | 160 | prompt | query ASR **+0.0563** (clears margin by 0.7 rows; **the cited control is withdrawn — C-20**) but only **37.5%** recovery; query refusal **−0.1562** (96.2% of the rise, back to within margin of clean) | PR-17, committed before the arms | `DonorPatch` at L14 over `query_span_positions` (24 positions) | ~~below-band L5 query patch: refusal 0.0000, ASR +0.0125~~ **WITHDRAWN (C-20): byte-identical to knockout-only on 160/160 rows. The +0.0125 is judge non-reproducibility on identical text (2/160), not an effect** | **S** (single-model) |
| C10 | The rescue instrument writes exactly what it read | Llama | smoke | 8 | row | identity vs arm **8/8 identical**; rescue vs identity **0/8** | byte comparison | `--rescue-donor self` | the two comparisons jointly exclude "never fired" | **verified** |


**⚑ R-168 — LOW ASR DOES NOT IMPLY NON-INSTALLATION (traced here for the first time).** Baseline mapped-win rate by dose: `main` 0.667/0.917/0.917/**1.000**, `ticket_bomb` 0.750/1.000/1.000/**1.000**, **`window_knife` 0.583/0.833/0.833/1.000**, `basket_gun` 0.333/0.417/0.417/**0.417**. **`window_knife` is decisive**: baseline ASR **2/96 and 1/96** across two judged runs — the lowest in the corpus — with installation saturating at **1.000**. A bank can teach the mapping completely and produce almost no successful attacks. `basket_gun` gives the other direction (never installs; C-31's 19/48, p=0.193). **No bank produces attacks without installing** — the cell that would matter for an objective is unobserved.

## 5. ⛔ Limitations that are properties of the BANK, not of the analysis

Two independent tests are **not constructible** here. Both need a new bank; neither is an analysis fix.

1. **Demonstration-specificity at the doses where the effect lives (R-25, quantified in R-48).**
   A count-matched non-demo control needs as many maskable non-demo positions as the demo block.
   **Measured:** demo is **~13 / 28 / 56 / 116 tokens** at `n_examples` 1/2/4/8, while the drawable
   pool is **30 tokens (`plain`) or 40 (role-wrapped)** — and the pool is **entirely chat template**,
   since nothing precedes `demo_block` and everything after it is the protected query.
   `match_ratio` is **1.0 at n=1, 0.875 at n=2, 0.000 at n=4 and n=8**. Rescoping to feasible rows is
   **forbidden** — demo length *is* the dose variable.
   **Fix built and it works mechanically (R-49):** `main_longpre` emits a neutral preamble OUTSIDE
   `demo_block`, giving `match_ratio` **1.000 (min and mean) at every dose**, pool 30 → 160, with
   `demo_block` byte-unchanged and `main` still regenerating byte-identically.
   ⛔ **But the fix costs the phenomenon, and that is now established rather than suspected
   (R-50 → R-52).** Baseline ASR **0.1562 (d10) → 0.0625 (preamble 12) → 0.0437 (preamble 10)**.
   Cutting the preamble to the principled minimum recovered **nothing measurable** (3 rows against an
   8.3-row margin), and on that bank both decisive doses fall **below the underpower threshold** (3
   and 1 attack rows) and are **DECLINED**. **The control can be built, and building it costs the
   attack it is meant to test — a trade that is NOT tunable by preamble length.**
   **Any future attempt needs non-demonstration context that does not dilute the attack**, which is a
   different design question from the one R-25 posed.
2. **Mapping-usage in free generation (R-27).** The concept vocabulary *is* the harmful content, so the
   flag is confounded with the outcome. **Fix: a codeword whose concept has a benign register.**

**Also:** every ASR here is the ASR of the **first 192 tokens**. Llama baseline is **93/160 (58%)** at
cap, `demoproc` **116/160 (73%)**. The untruncated Llama subgroup holds **0-7 baseline attacks** and
cannot test robustness. **Qwen3 is only 26% truncated, its both-EOS subgroups are 111/114 rows, and
every effect survives there at full size** — the cross-model claims rest on the less-truncated model
(DR-2). Re-running at a larger cap would change the measured quantity and break comparability.

## 6. Answers to §20's success questions

| # | Question | Answer |
|---|---|---|
| 1 | Caused by response-query retrieval, or by prefill corruption? | **Neither exclusively.** All four scopes remove indistinguishable amounts **at n=160** (C3); **at n=96 `respq` separates from `demoproc` by 8 rows in both models — C-69**. The prefill/demo scope is distinguished only by **restoring refusal** (C1). |
| 2 | When suppressed, **what changes**? | **Coherent non-compliance** in every arm (C4), plus **restored refusal** in `demo_processing_only` alone (C1). Not degeneration; not loss of binding (C5). |
| 3 | Causal rescue by activation patching? | **RUN, and REPLICATED across a complete 2x2 (R-35/36/37/38).** PR-13 Outcome C on ASR for Llama; Handing back clean demo-position activations at L14 recovers only **16.7%** of the ASR effect (within margin of knockout-only), but removes **69.2%** of the refusal rise (35→17 rows, >2× margin); the below-band L5 control moves refusal by **0.0000**. **The two effects have different substrates, shown causally on both models.** ⚠ A Qwen3 ASR rescue appeared on pool A (+0.0625) and **FAILED its pre-registered confirmatory test on pool B** (+0.0437, needed >0.0521 — missed by ~1.3 rows of 160). **Not promoted; see R-37.** |
| 4 | Low-rank or distributed? | **NOT RUN, and now differently motivated.** Q3 returned a null on ASR, so there is no successful full-state ASR rescue to decompose. The live question is instead what carries the **refusal** effect, which L14 patching *does* move. **Open.** |
| 5 | Fourth demonstration pool? | **ANSWERED — C1 replicates (R-29).** Pool B shares **0 of 40** sentence sets with pool A; `demoproc` rise **+0.1938** (3.7× margin), other scopes within margin. Domain expansion also delivered (R-18: k 6→10, floor 0.0625 → 0.00195). |
| 6 | Codeword/concept factorization on Qwen3, joint crossed? | **NOT RUN.** **Open.** |
| 7 | Llama retrieval/refusal independence on Qwen3? | **ANSWERED, and it replicates** (C1, C2) — refusal restoration is Qwen3-present, and its independence from attack removal is Qwen3-confirmed. |
| 8 | Legitimate GCG/MAC objective? | **BLOCKED and correctly so.** No stable, specific, transferable low-dimensional handle was produced. |

## 7. Next decisive experiment

**Build the longer-context bank.** It unblocks the *only* structurally missing control (C7 →
demonstration-specificity at n_examples 4 and 8), and the same bank redesign can carry a
benign-register concept that unblocks R-27. Everything else in this phase is measurement on artifacts
that already exist; **these two are the questions this bank cannot answer at any sample size.**

Second: **activation-patching rescue (§20 Q3)** — but reframed. Its original target was the retrieval
representation; after C-12 the interesting target is *what carries coherent non-compliance*, which
this phase measured (C4) and did not explain.

## 8. Canonical artifacts

| what | path |
|---|---|
| bank (10 domains), sha256[:16] `368566acecdc350f` | `data/boombness_prompts/boombness_prompt_bank_d10.jsonl` |
| Llama arms / judge | `outputs/boombness/score_behavior/p4b*_20260825_*` · `outputs/boombness/judge/p4bj_*_20260825_*` |
| Qwen3 arms / judge | `outputs/boombness/score_behavior/q4b*_20260825_*` · `outputs/boombness/judge/q4bj_*_20260825_*` |
| non-demo controls | `outputs/boombness/score_behavior/p5_capped_d{1,2,3}_*` · `outputs/boombness/judge/p5j_capped_d*` |
| decomposition estimator output | `outputs/boombness/phase1_decomposition/p4bdec_20260825_113813_3430676/` |
| kill-route breakdown | `outputs/boombness/kill_route_breakdown/krb_20260825_131040_3620206/` |
| within-family bridges | `outputs/boombness/binding_behaviour_bridge/bridge_20260825_101613_3117657/` (Llama), `qbridge_20260825_104155_3190213/` (Qwen3) |

**Judge provenance is closed on every behavioural result:** `judge_model_used = openai/gpt-4o-mini` on
**800/800** rows per model and **480/480** for the controls, with `completion_sha256_16` joining the
generation on every row. Bank provenance verified at **content level** (per-row `prompt_sha16`) on
**13/13** arms, 0 mismatches (DR-2).

## 9. Reproduction manifest (§19-E) — one command per result

All use `/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`. Analyses are CPU-only
and read committed artifacts; the arms need SLURM + GPU.

| result | command |
|---|---|
| bank (byte-identical) | `python src/boombness/prompt_families.py --pools data/boombness_prompts/demo_pools_d10.json --preset main --codeword carrot --concept bomb --seed 20260825 --strict --out <out>.jsonl` |
| bank audit | `python src/boombness/tokenization_audit.py --bank data/boombness_prompts/boombness_prompt_bank_d10.jsonl` (needs the HF cache → run on a compute node) |
| behavioural arms | `sbatch --export=ALL,BOOMB_SCRIPT=score_behavior.py,BOOMB_ARGSFILE=$PWD/runargs/p4b/<arm>.txt src/boombness/slurm/run_boombness.sh` (argsfiles committed under `runargs/p4b`, `runargs/q4b`, `runargs/p5`) |
| judging | `sbatch --export=ALL,P2_MANIFEST=...,P2_PREFIX=p4bj,P2_EXPECT_ROWS=160,P2_BANK=...,P2_PIN_JUDGE_MODEL=openai/gpt-4o-mini src/boombness/slurm/run_p2_judge.sh` ⚠ **not** `run_judge_cpu.sh`, which ignores every `P2_*` variable |
| C1/C2/C3/C8 decomposition | `python src/boombness/phase1_decomposition.py --baseline A=<judge> --arm <lab>=<judge> ... --gens <lab>=<gens> ... --tag p4bdec` |
| C4 kill routes | `python src/boombness/kill_route_breakdown.py --cell <model>:<arm>:<judge_base>:<judge_arm>:<gens_arm> ... --tag krb` |
| C5 within-family bridge | `python src/boombness/binding_behaviour_bridge.py --bank data/boombness_prompts/boombness_prompt_bank.jsonl --beh-baseline <p1k_A> --beh-arm <lab>=<p1k_*> --probe-baseline <p2A> --probe-arm <lab>=<p2_*> --tag bridge` — ⚠ **the bank MUST be the one those runs came from.** The carrot bank's ids are a strict subset of d10's, so a mismatched pairing silently drops rows; the script now refuses it (C-13) |
| C9 rescue arms | `sbatch --export=ALL,BOOMB_SCRIPT=score_behavior.py,BOOMB_ARGSFILE=$PWD/runargs/p7/p7_rescue_L14.txt src/boombness/slurm/run_boombness.sh` (argsfiles: `runargs/p7`, `runargs/p8`) |
| C10 identity control | same, with `--rescue-donor self` in the argsfile (`runargs/p7/p7smoke_identity_L14.txt`) |
| **C9 / C11 / C12 table** | `python src/boombness/rescue_dissociation_table.py --cell NAME:BASE:KNOCK:RESCUE:CONTROL [--cell ...] [--n-examples 8] --tag c9` — emits rows, margin-in-rows, ×margin, control and percentage together. **Verified 2026-08-26 to reproduce DR-5's hand audit exactly** (18/2.16×, 17/2.04×, 12/1.44×, 18/2.16×, 25/3.00×, C12 4/1.92×, all controls 0) |
| **C6 / C7 per-dose breakdown** | `python src/boombness/dose_breakdown.py --baseline <judge> --arm LABEL=<judge> [--gens LABEL=<gens>] --tag dose` — emits cell size, margin-in-rows, **both** ASR and refusal, and `control_draw_match_ratio` per dose. **Verified 2026-08-26** to reproduce R-22 (Llama `[0,3,9,14]` monotone; Qwen3 `[7,1,5,8]` non-monotone) and R-26 (n=2: demoproc −5 of 5 attacks vs capped mean −0.67, match ratio 0.989; 0.547 / 0.272 at n=4 / n=8) |
| all deliverable guards | `python src/boombness/check_all.py` |
| full suite | `python -m pytest tests/ doublespeak_causality/tests/ -q -p no:randomly` — **serial and exclusive** (C-2: concurrent runs corrupt committed artifacts) |

**Known repo hazards, carried here so they are not rediscovered:** `run_judge_cpu.sh` silently
discards `P2_*`; zsh does not glob unquoted parameters (build arg lists in Python); `--seed` is inert
at `--preset main`; `--export` truncates comma values; the full test suite mutates committed files and
must not run concurrently.

---
---

# ADDENDUM — Representation–Behavior Dissociation (RBD) confirmatory sprint, 2026-08-29/30

**Everything above this line belongs to the 2026-08-25 behavioral-causality phase and is unchanged.**
This addendum is a *separate* sprint with its own id namespace (`RBD-PR / RBD-R / RBD-C / RBD-DR`),
deliberately disjoint from the four colliding registries this repo already carries. **Never write a
bare `C-12` or `R-25` when citing it.**

* **Authoritative log:** `external_md/REPRESENTATION_BEHAVIOR_DISSOCIATION_CONFIRMATORY_SPRINT_PLAN_AND_PROGRESS.md`
* **Claim ledger:** `reports/rbd_claim_ledger.json` · **Main table:** `reports/RBD_MAIN_TABLE.md`
* **Starting commit:** `10fcd035`

## 1. The one-paragraph truth

The sprint asked whether a scoped intervention can **preserve an installed semantic mapping while
removing the behaviour built on it**. **It cannot — on either model.** `demo_processing_only`
**damages the representation**: binding falls −0.2125 on Llama-3.1-8B and **−0.8250 on Qwen3-14B**,
while **the identical scope at a late band is exactly inert — on the binding readout of
`lantern_poison`, on both models** (Δ = 0.0000, zero discordant pairs). ⚠ **That control is NOT
inert on benign use, on ASR, or on `candle_missile` binding** (see §2). The dose is exactly matched:
arms B and C have identical `total_prefill_edits` within each bank. **Outcome A is excluded on the binding conjunct alone.** The behavioural half could not be
measured at all — baseline attack rates of 12/160 and 5/160 against a preregistered floor of 14 — so
it is **DECLINED on both models**, and **no claim about attack suppression exists anywhere in this
sprint.**

## 2. ESTABLISHED

| # | claim | evidence |
|---|---|---|
| **`RBD-R-025`/`R-032`** | **`demo_processing_only` does NOT preserve binding**, on both models | Llama 78→61 (Δ −0.2125, envelope [−0.3162, −0.1166], 18 lost / 1 gained, p 7.6e-05); **Qwen3 75→9 (Δ −0.8250, 66/0, log-odds +16.62 → −4.99)**. ⚠ **The Llama upper bound clears the margin by 1.3 of 80 families — two families moving would flip it to `NOT_ESTABLISHED`. Qwen3's is decisive. "Failed on both" must not imply equal weight.** Late-band control **78→78 and 75→75, Δ exactly 0.0000, zero discordant pairs — on the BINDING readout of `lantern_poison` only** (see below). |
| **`RBD-R-029`** (⚠ **LLAMA ONLY**) | **Installation without use.** Llama reports the mapping and does not apply it | binding 78/80; property known 80/80 (`direct_harmful`); benign use **24/80** — **no better than the no-mapping control (32/80)**; the instrument's
no-mapping null is ~0.40, NOT 0.50, so this is *absence of composition*, not active avoidance |
| **`RBD-C-012`** ⚠ **DOWNGRADED** | Qwen3 and Llama differ **sharply in raw mapped-option rate**; the *composition* reading is **not established** | **Qwen3 69/80 vs Llama 24/80** — raw difference **+0.5625, Newcombe CI [0.4208, 0.6695]**, Fisher p 3.3e-13. Same bank, demonstrations and question. ⚠ **`RBD-C-016`: both `*_allcond` control runs are LLAMA-ONLY.** No `benign_literal` / `direct_harmful` condition was ever run on Qwen3, so Qwen3's *mapping-attributable lift* — the quantity "composition" names — **is not estimated**, and Readout B's validity is established on Llama only. On Llama the lift is indistinguishable from its own no-mapping control (24/80 vs 32/80, McNemar **p = 0.215**). Sensitivity: a Qwen3 null of ≥61/80 would drop its lift below the 0.10 margin. **The raw model difference is solid; the mechanism label is not.** |
| **`RBD-R-036`** ⚠ **DOWNGRADED TO OBSERVATION** | Baseline ASR on `rbd12` is **low**; the attribution **to concept** does NOT hold | `poison`/`missile` give **0.075** (Llama) and **0.031** (Qwen3). ⚠ **`RBD-C-017`: my "same design, dose, domains, cap and judge" control clause is FALSE ON EVERY CLAUSE.** vs the prior bomb banks the comparison changes **domains (the two sets are 100% DISJOINT)**, role-style composition (1 vs 6), demo pools, dose (`{8}` vs `{0,1,2,4,8,16}`), **generation cap (640 vs 192)**, and judge pinning (pinned vs *unknown responder*). Worse, **this repo already records bomb-bank baselines of 0.0437–0.0625 from a two-sentence preamble change alone** — a 3.6× swing *within* `bomb`, larger than the gap being attributed to concept, and `rbd12`'s 0.075 sits **inside** it. "0.15–0.28" selects the top of the bomb range. **"Cross-model replicated" is also unsupported** — there is no Qwen3 bomb comparator; what replicates is the low `rbd12` rate, not the contrast. **Concept is a plausible but UNIDENTIFIED contributor.** The direct test (`RBD-PR-005`) was never run. |
| **Readout B is a valid instrument** | measures mapping *use* without touching harm | **1.000/0.950 when the concept is named directly** (`direct_harmful`); option mass **0.6048–1.0000** across the 18 readout runs (0.64–0.95 is the **Llama baseline+control** subrange; ⚠ **`RBD-C-018`: "0.64–0.95 on every core run" was a universal quantifier my own correction pass attached to a Llama-only range — false as written, and it sat in the row that certifies the instrument**). ⚠ **`RBD-C-015`:** the "0/80 with no mapping taught" validation belongs to the **BINDING** readout, not Readout B — Readout B under `benign_literal` reads **32/80** (`lantern_poison`) and 0/80 (`candle_missile`). |

⚠ **`RBD-C-015` scope correction — "the late-band control is exactly inert on both models" is TRUE
ONLY for the BINDING readout on `lantern_poison`.** It is **not** inert on benign use (Llama
24→23, Qwen3 69→67), on ASR (pooled Llama 12→16, Qwen3 5→7), or on `candle_missile` binding
(Llama 52→49, n10=3). The dose-matching *is* exact — arms B and C have identical
`total_prefill_edits` per bank — so the band, not the dose, is what differs.

## 3. FAILED / DECLINED / VOID — and why each is which

* **H1 → Outcome A EXCLUDED**, on conjunct 2 alone, independently of everything else.
* **Behavioural estimand → DECLINED (Outcome E)** on both models. ⚠ **Llama arm B passed every T2
  criterion** (12→1, Δ −0.0688, 11 rows, cluster p 0.00635, control moving the opposite way) **and is
  still declined**, because 12 baseline attacks is below the headroom floor fixed before any data
  existed. **Its Qwen3 counterpart is −3 rows at p = 0.625.** That contrast is what an underpowered
  design looks like.
* **T5 (benign mapping-use) → VOID on all Llama cells** — no baseline use to disrupt. **Measurable on
  Qwen3**, where arm C is `EQUIVALENT` and arm B is `NOT_ESTABLISHED`.
* **`candle_missile`** — ⚠ **corrected by `RBD-C-015`**: **Llama PASSES T4 there** (52/80 vs
  `critical_k` 50) and returns **`NOT_ESTABLISHED`** (Δ −0.1250, envelope [−0.2250, −0.0305],
  crossing the margin). It is **set aside POST HOC** on `RBD-R-028`'s destructive-control
  incoherence — **a data-derived criterion, not a preregistered gate**. Only **Qwen3** ×
  `candle_missile` is **T4-VOID** (40/80 = exactly chance). ⚠ The set-aside cell is the one that
  *least* supports the headline, so the exclusion is outcome-favourable and must be labelled as
  post hoc wherever it is used.

## 4. MERELY EXPLORATORY / UNRESOLVED

* **`RBD-R-033`** — on Qwen3 the intervention destroys *reportability* (75→9) far more than *use*
  (69→56): a dissociation in the **opposite orientation from H1's**. **NOT ANSWERABLE** with this
  project's instruments. Two attempts (`semantic_one_word`, `comprehension_usage`) both **fail the
  option-mass gate on the decisive cell**.
  **The structural reason, which is the reusable finding:** a readout that **names its options** is
  high-mass **and** exposure-confounded; one that does not is exposure-clean **and** unreportable.
  **No readout in this inventory is both.**
* **`RBD-R-030`** — masking the demonstrations is **not** equivalent to not having them
  (`benign_literal` 0/80 vs `legacy_all_query` 63/80 on one cell).

## 5. ⛔ MUST NEVER BE QUOTED

1. **Any claim that `demo_processing_only` suppresses the doublespeak attack.** The estimand is
   DECLINED on both models. The T2 arithmetic passing does not change this.
2. `candle_missile` as **"VOID on both models"** — ⚠ **Llama PASSES T4 there** (52/80 vs critical 50)
   and returns **`NOT_ESTABLISHED`**; it is set aside **post hoc** on `RBD-R-028`, not by a gate.
   Only **Qwen3** × `candle_missile` is T4-VOID. Nor may its T3 delta be quoted as a replication.
3. Any **T5** verdict on a Llama cell — VOID for absence of baseline use.
4. `legacy_all_query` as "the no-mapping control" (`RBD-R-030`).
5. **`RBD-R-029` as a general claim about composition** — it is Llama-specific (`RBD-C-012`).
6. The below-gate `PR-007`/`PR-008` numbers (18→0, 8→9, 52→0). They sit in a 0.2–4% option-mass tail. ⚠ **`RBD-C-019`:
   "no gate was overridden" is literally FALSE — all four of those runs record
   `option_mass_gate = "OVERRIDDEN — NOT REPORTABLE"` in their own `summary.json`. The defensible
   statement is that **no gate-failing number was used to support a claim.**
7. **T7 (`n_examples=16`) as a headroom remedy** — uninformative by construction (`RBD-C-011`).

## 6. The exact next experiments

1. **Screen behavioural headroom on a DEVELOPMENT population before committing to a lexical pair.**
   This sprint's H2 rule correctly excluded ASR from *selection*; the cost was that headroom was left
   to chance and failed on **all four cells**. Add a prior, separate screening stage — it preserves
   outcome-blindness where it matters (the confirmation) without spending a matrix on a population
   that cannot answer. **This is the single most actionable methodological finding.**
2. **Resolve `RBD-R-033` at the ACTIVATION level, not with another readout.** Patching does not
   depend on what the query mentions, so it sidesteps the mass-vs-exposure trade entirely. The
   `donor_patch` infrastructure already exists.
3. **Re-run the confirmatory design with a headroom-screened concept** (e.g. `bomb`-class) on the
   same 20 held-out domains. The whole apparatus — banks, presets, readouts, analysis, verifier — is
   built and tested; only the pair changes. ⚠ Do this as a **new** confirmation, not as a rescue of
   the declined estimand.
4. **Ask whether the HARMFUL route composes the mapping where the benign route does not** (Llama).
   `RBD-R-029` shows stage 1 reached and stage 2 not, under a *benign* query. Whether the attack
   query composes is the sharp open question — and it needs a population with headroom, i.e. (1)
   first.

## 7. Reusable assets built here

`src/boombness/paired_equivalence.py` (the equivalence test the repo lacked — Newcombe + cluster
bootstrap, conservative envelope, rule-of-three capability) · `rbd_bank_audit.py` (independent bank
audit, does not import the generator) · `rbd_analysis.py` (preregistered analysis, committed before
the data) · `scripts/rbd_verify_independent.py` (imports **none** of the producers; agrees with them
on 6,000 random cases) · `scripts/rbd_build_judge_manifest.py` (refuses an incomplete input run) ·
`scripts/rbd_submit_wave.sh` (enforces the SLURM caps in code) · Readout B
(`mapping_use_forced_choice`) · `asr_protocol`'s **completion-hash join, which was documented but
never implemented** before this sprint.

## 8. Hazards worth inheriting

* **Each intervention arm has its OWN liveness contract.** `legacy_all_query` legitimately produces
  ~34M decode edits; `demo_processing_only` legitimately produces none. Applying one scope's
  must-be-zero rule to every arm produced a false alarm **three times** (`RBD-C-010`).
* **Pipeline automation and manual execution are mutually exclusive** — running both produced
  duplicate judge jobs (`RBD-C-013`), caught before any artifact existed.
* **Any preregistration clause naming `n_examples` must state its resulting family count and row
  total when written.** Two registered decisions were wrong for want of that check
  (`RBD-C-004`, `RBD-C-011`).
* **A self-derived expectation is not an expectation.** An audit whose expected counts come from the
  rows it is checking will certify a bank missing an entire domain (`RBD-DR-002` F3).

---
---

# ADDENDUM — Representation Access & Headroom (RAH) sprint, 2026-08-30/31

**Branch `behavioral-causality-sprint`, `fe8fd610..f9729af2`.** Unique id namespace `RAH-PR / RAH-R /
RAH-C / RAH-DR`. **Never write a bare `C-12` or `R-25` when citing it.** Full log:
`external_md/REPRESENTATION_ACCESS_AND_HEADROOM_NEXT_SPRINT_PLAN_AND_PROGRESS.md`. Standalone
summary: `reports/RAH_SPRINT_SUMMARY.md`. Every number below is re-read from its raw artifact by
`reports/RAH_REPRO_MANIFEST.json`, **executed on a clean tree: 17 numbers, 5 verifiers, 0 failures.**

## 1. The one-paragraph truth

The predecessor sprint said the route out of its dead end was activation-level patching. **That route
was built and run to a held-out conclusion, and it returned CANNOT ANSWER.** Along the way the sprint
established that the doublespeak mapping is **installed and not used** (4/4 cells), that the
**80-row-per-arm design used throughout this project cannot detect a behavioural effect of any size**
once judge noise and domain clustering are counted, and that the one re-run patchscope failure in this
repository failed for a **fixable reason** — the receiver injection layer, worth 31–130× on
**Llama**. **Six further recorded failures were not re-run, and the effect is not model-general.** Both tracks closed on preregistered negative or non-answerable outcomes; **no
intervened arm was interpreted on either.**

## 2. ESTABLISHED

* **The mapping is installed and is not used, 4/4 cells** (`RAH-R-004`). Binding lift **+0.5000 …
  +0.9750**, every CI excluding zero; benign mapping-use lift **NOT ESTABLISHED** on all four. Not a
  power failure — on `candle↔missile` the readout has a 76-row dynamic range and the doublespeak arm
  sits at 2.6 %/3.9 % of it. n = 80 families, 20 domains, paired, independently re-derived.
* **`RBD-C-016` is CLOSED.** Qwen3's 69/80 mapping-use rate is **not** mapping-attributable: its
  no-mapping base rate on the same families is **72/80 — higher**. The Llama-vs-Qwen3 difference is a
  difference in **base rates for the option words** (0.40 vs 0.90), not in mapping use.
* **The 80-row design is structurally underpowered** (`RAH-R-006`). At k=20×m=4 the MDE is `n/a` at
  every baseline this repo has measured — *even reducing ASR to zero misses 80 % power*. At n=160 and
  baseline 0.15 it is still `n/a`, so meeting the old 14-attack floor would not have rescued it.
  **Domains, not rows, are the binding lever.**
* **Judge flip rate RISES with baseline ASR** (`RAH-C-004`): 0.021 at ASR 0.013 → 0.085 at ASR 0.27,
  measured with `effective_flip_rate` per population. A higher-headroom population does **not** buy
  proportional power.
* **The ONE re-run patchscope failure was the receiver injection layer** (`RAH-R-008`), **on Llama**.
  R=28 → R=4 of 32: archived config **0.0088 → 0.2771 (31×)**, best form **0.0065 → 0.8421 (130×)**;
  ⚠ each endpoint is a max over 31 donor layers with **differing argmax layers**, and at a fixed
  layer the ratio is 16.5–321.8×. ⚠ **Not model-general**: on Qwen3 `fc_probe_last` passes at **all
  five depths including `n_layers − 4`**, so *"an early injection layer is necessary"* is false there.
* **Fresh judge-noise measurement** (`RAH-R-007`): **11 flips / 299 freshly-judged byte-identical
  rows = 0.0368**, pinned model, same commit. This **replaces** the repo's 6.5–7.0 % per-invocation
  figure, which has **no committed artifact** behind it.

## 3. FAILED / DECLINED / CANNOT ANSWER

* **Track A → A-IV, CANNOT ANSWER** (`RAH-R-018`). Both viable configurations closed: the one
  selected on the positive control transports the **codeword**, not the concept; the one selected on
  baseline transport is **unreportable on held-out material** (median option mass **7.147e-08**
  against a 0.05 gate, **0/80 rows** above gate, every arm). No Δ computed, no equivalence test run.
* **Track B → B-BLOCKED-BY-MATERIAL** (`RAH-R-021`). One screening cell of four qualifies and it is
  the **discovery pair on a single model**; there is **no qualifying cell on Qwen3 at all**. The
  confirmatory matrix was **not run** and ≈20 GPU-hours were not spent.
* **`RBD-PR-005` executed as registered and CLOSED** (`RAH-R-007`): pooled ratios 1.57× (Llama) and
  1.00× (Qwen3) against preregistered MDEs of 2.68× and 4.10×. **Does not move at a resolvable
  size** — licenses *"no LARGE dose effect"*, never *"no dose effect"*.

## 4. UNRESOLVED / DIAGNOSTIC ONLY

* Whether the exposure/mass dilemma is **general** at the activation level. Observed **once**, one
  model, one bank, n = 80 (`RAH-C-015`).
* The `bomb` > `knife` pair effect — 1.79× (Llama) and 2.20× (Qwen3) with domains, cut, dose, cap,
  judge, window and models all matched. **Codeword and concept change together**, so it is a *pair*
  effect and cannot be attributed to the concept alone.
* Refusal rates differ sharply by pair — **0.217/0.270** on `ticket↔knife` vs **0.013/0.020** on
  `carrot↔bomb`. A plausible mechanism for the ASR gap. **Recorded, not interpreted.**
* The full-suite vs guard-list order dependence inherited from before this sprint (`RAH-R-016`).

## 5. ⛔ MUST NEVER BE QUOTED

1. **The Track-A argmax shift.** Held-out `base` → `poison 36`, `dpo` → `poison 0` looks like a large
   clean intervention effect and is computed over probabilities of order **1e-8**, six orders below
   the reportability gate. Recorded in `RAH-R-018` **as NOT USED**.
2. **"~96×"** for the receiver-layer improvement (`RAH-DR-003` A3) — it crosses two receiver forms
   and two donor layers. Like-for-like it is **31×** and **130×**.
3. **"0.1562"** as the `carrot↔bomb` screening baseline (`RAH-C-014`) — that is pooled over
   `n_examples` {1,2,4,8}. The screening population is **0.1645**.
4. **"all five prior patchscope failures were the receiver layer"** (`RAH-DR-003` A5) — there are
   **seven** artifacts, two used `n_layers−2`, and **only the one archived configuration was re-run**.
5. **Any R-profile statement as model-general** (`RAH-DR-004` B3) — the profile is **Llama's**. On
   Qwen3 `fc_probe_last` passes at all five depths **including `n_layers − 4`**, and `id07_tmpl`
   passes only at R=20. *"An early injection layer is necessary"* is **false on Qwen3**.
6. **"the depth fraction transfers across models"** (`RAH-DR-004` B3) — both `R_set`s were laid out
   at identical depth fractions **by construction** and the rule tie-breaks on the lowest. Agreement
   of a **selection rule**, not a demonstrated depth effect.
7. **"same donor"** for the 31×/130× ratios (`RAH-DR-004` B2) — each endpoint is a maximum over 31
   donor layers with a **different argmax layer**. At a fixed layer the ratio is 16.5–321.8×.
8. **"5 independent verifiers"** (`RAH-DR-004` B4) — it is **2 independent + 3 replay checks**; the
   replays originally discarded their output and proved only that a script had not crashed.
9. **`exch` as a specificity control** (`RAH-DR-003` B1) — it is a *permutation* of `base` and cannot
   differ on any aggregate. Paired per-family only.
10. **The capped key control as "dose-matched"** (`RAH-R-011`) — it masks **23.2 %** of the demo dose;
   strict count-matching is **infeasible** on this population.
11. **"N passed" from the pre-commit hook as "the suite is green"** (`RAH-R-016`) — it is *"the guard
   list is green"*, strictly weaker, and the full suite is known to disagree with it.

## 6. The exact next step

**Track B is blocked by a BANK, not by an experiment.** Build a **38-domain bank on a NEW lexical
pair with a bomb-class concept** — this needs fresh demonstration pools across 38 domains. With it,
k=38 × m=16 at baseline ≥ 0.1375 reaches an MDE of **0.70 relative**, enough for the 73 % reduction
the discovery bank showed, with little to spare. Screening is cheap (baseline arm only, 152 rows per
cell); the confirmatory matrix is ≈20 GPU-hours and should be a **separate, costed decision**.

**Track A needs a receiver that is both exposure-clean and high-mass on held-out material.** No such
readout exists in this project's inventory at *either* the behavioural or the activation level. That
is now a **characterised** open problem rather than a suspicion, and it is the single most valuable
thing to solve.

## 7. Reusable assets

`rah_preflight_transport.py` (donor×receiver×layer sweep, three-conjunct gate, **no intervention code
path** so any selection made with it is structurally effect-blind) · `rah_transport_assay.py`
(arm-active capture, per-row vacuity, key-presence liveness, variant dedup) · `rah_power_trackb.py`
(clustered power, measured ASR-dependent flip rate) · `rah_verify_phase1.py`, `rah_verify_dose.py`
(stdlib-only independent verifiers) · `rah_select_config.py`, `rah_select_transport_config.py`,
`rah_screen_table.py`, `rah_make_gatesub.py` (deterministic unit-tested rules that **refuse** rather
than degrade) · `rah_repro_manifest.py` (a manifest that **executes**).

## 8. Hazards worth inheriting

* **Validating an instrument on a positive control does not make it the right instrument.** The
  positive control here captures where the concept is *literally present* — close to a copy test —
  and it selected the form that was **worst** for the real question (`RAH-R-014`).
* **A donor layer at or below the knockout band makes the arms BIT-IDENTICAL**, and every validity
  gate still passes because none of them sees the intervened arm (`RAH-DR-001` F2). Constrain
  `L > lo` and **measure** the delta per row.
* **A late-band control is vacuous at a fixed mid-depth capture site**, and a count-matched key
  control is **infeasible** when the demo block exceeds the protected complement. Both dose-matched
  controls can be unavailable at once, for independent reasons.
* **Resolvers should raise and required fields should be referenced by key.** Three crashed smokes
  this sprint were each a genuine defect made **loud**; under `.get(k, default)` all three would have
  been silent wrong numbers.
* **Smoke every MODE and every CONFIGURATION, not just every script** (`RAH-C-009`, `RAH-C-013`).
* **An unchanging test count is a signal.** "294 passed" never moved because new guard tests were
  never in the hook's list (`RAH-R-016`).
* **The numbers keep being right and the sentences keep being wrong.** Every claim-level defect this
  sprint found in its own work was a **scope** error, not an arithmetic one — a property of one
  configuration written as a property of a position, a level-B number defending a level-A null, a
  pooled rate quoted as a subset rate.
