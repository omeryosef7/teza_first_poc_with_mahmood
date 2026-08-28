# Demonstration Retrieval → Behavioral Causality — plan, decision gates, and live progress log

**File:** `external_md/DEMONSTRATION_RETRIEVAL_BEHAVIORAL_CAUSALITY_NEXT_PHASE_PLAN_AND_PROGRESS.md`
**Opened:** 2026-08-25 00:30 IDT
**Repo:** `first_poc/teza_first_poc_with_mahmood`, branch `behavioral-causality-sprint`
**HEAD at open:** `059e819f` ("C-18 code closure: four defects fixed and verified; the tool now warns
about its own statistic", 2026-08-24 23:53:54 +0300)
**Owner of this phase:** this Claude session. SLURM submissions for this phase are owned here and
logged in §B4.

> **This file is the authoritative live research log for this phase.** Part A (the plan) is **stable**
> and is not rewritten as results arrive. Part B is **append-oriented**: superseded conclusions are
> marked `⛔ RETRACTED — reason` with the corrected statement beside them, never silently overwritten.

> **Concurrency.** A peer Claude session (`BOOMBNESS_D_SURFACE_FOLLOWUP implementation`) owns the
> previous phase's log (`external_md/BOOMBNESS_DSURFACE_NEXT_PHASE_PLAN_AND_PROGRESS.md`) and
> `src/boombness/crossbank_knockout_test.py`, and had jobs **779083–779086** (Phase 10b, `button_gun`)
> in flight when this file was opened. **This session does not touch those files or those jobs and does
> not run `scancel`.** Staging is by explicit path; `git add -A` is forbidden here.

---

## ⚠️ READ THIS FIRST — LIVE CLAIMS LEDGER *(initialised 2026-08-25 00:30)*

**Nothing in this phase has produced a result yet.** The rows below are the **inherited** state this
phase starts from, carried in so that no figure is quoted from the previous phase without its current
status attached. Every row names the correction that last touched it.

### ✅ LIVE — what currently stands (inherited)

| claim | evidence | where |
|---|---|---|
| ⛔ **PR-11 UNINFORMATIVE — instrument confounded with outcome.** Concept usage falls 64%/81% (baseline jailbroken) to 0-11% (killed), but baseline **NOT-jailbroken** rows sit at **6%/10%** — killed rows look like untreated non-jailbroken ones. In this bank "mentions bomb" and "is a jailbreak" are near-identical events. **No mapping-usage claim made; R-16/R-17 neither supported nor contradicted** | the pre-committed confound clause is the only reason this is a null and not a headline | **R-27** |
| ⚠️ **EVERY ASR HERE IS THE ASR OF THE FIRST 192 TOKENS.** Llama baseline **93/160 (58%)** at cap, demoproc **116/160 (73%)**; the untruncated Llama subgroup holds **0-7 baseline attacks** and cannot test it. Qwen3 is 26% truncated, its both-EOS subsets are **111/114 rows**, and every effect survives at full size | provenance 13/13 arms verified at content level, 0 sha mismatches, 0 duplicate tags; suite 1358/0 | **DR-2** |
| ⚖️ **ONE matched, powered demonstration-specificity cell exists — at n_examples=2, where the capped control is 0.989-matched.** `demoproc` removes **5/5** attacks; the control removes **0.67/5** across three independent draws; gap **0.1083**, 2.6x the margin. Under-matched at n=4 (0.547) and n=8 (0.272), so those stay UNTESTED. Suggestive, one dose, 5 attacks, one model | capped arm read one-sided per PR-10; the overall null is NOT quoted as support | **R-26** |
| 🏆🏆🏆 **C7 RESOLVED (Qwen3), REPLICATED on an independent pool, and TRUNCATION-ROBUST.** Pool A: `demoproc` **5/5** at n=4 and **5/7** at n=8 (−0.1250 each), controls **1,2,2** and **2,−2,−1**, separation **2.0x**/**3.2x**. Pool B: **−4/4** and **−5/6**, controls **+1,+1,+1** and **0,−1,−2**, separation **3.0x**/**1.8x**. **Untruncated (640-token cap, 0.000 stop-on-length on every arm): −3/4 and −7/7, control +1 and +0, separation 2.4x/4.2x** — the effect is **the same size at both caps** — a within-row test shows the cap moves neither arm detectably (baseline 3↓/4↑, demoproc 1↓/1↑, both p=1.0; **C-23**), so the truncation-artifact hypothesis is unsupported without claiming growth. match_ratio 1.000 on every control row throughout; draws distinct by seed AND generation hash | **R-58** (PR-23) + **R-62** (PR-25) + **R-64** (PR-26); **C-19 discharged**; Llama remains **declined for power**, not refuted; n=4 untruncated is the thinnest cell at **1.4x** margin | **R-58**, **R-62**, **R-64** |
| ⛔ **PR-23 GATE FAILED (C-18): the Qwen3 control is NOT constructible at n=8 on either preamble bank** — Qwen3 pool **112/133** vs a 114-token demo block, so the arms refused before generating. R-49/R-51's feasibility was a **Llama** measurement (`--model` defaulted); the claim was generalised to a method it never covered | arms produced no generations; nothing to salvage | **C-18** |
| ⚖️ **C13 IS LLAMA-SPECIFIC (PR-22).** Qwen3 d10 **21/160** vs longpre10 **23/160** — gap **+2 rows**, inside margin and pointing the wrong way, on **21 baseline attacks** (powered) with **0 rows** of drift. 🟢 **Consequence: C7's power blocker is Llama's, not the method's — Qwen3 keeps its attack on the preamble bank where match_ratio is 1.000 at every dose** | **R-54** | **R-54** |
| 🏆 **NEUTRAL CONTEXT SUPPRESSES THE ATTACK: ~10 sentences touching neither demos nor query cut ASR by two thirds** (27/160 → 6/160 same-window, −21 rows vs a 8.3-row margin), with cross-session drift measured at **2-4 rows** and the banks verified to differ *only* by the preamble | **R-53** (PR-21); withdrawn as unestablished in C-15, then established | **R-53** |
| ⛔ **THE PREAMBLE PATH IS A DEAD END FOR C7.** Making the control constructible costs the attack: baseline ASR **0.1562 (d10) → 0.0625 (pre12) → 0.0437 (pre10)**, and cutting the preamble on a principled criterion recovered **nothing** (3 rows, inside noise). Both decisive doses on pre10 are **DECLINED as underpowered** (3 and 1 attack rows vs the rule's 4) | **R-52**; the trade is not tunable by preamble length | **R-52** |
| ⚖️ **C7 TESTED AT LAST — AND STILL UNRESOLVED.** PR-19 required both n=4 and n=8; **n=8 holds all three conditions** (demoproc −0.1000, controls +0.0000/+0.0500/+0.0000, separation **2.8x margin**) while **n=4 fails** (a control removed as much as demoproc). Both cells rest on **4 baseline attacks of 40**, and the preamble halved baseline ASR (0.1562 → 0.0625) | **R-50**; the fix that enabled the test also weakened the attack | **R-50** |
| 🏆 **C7 UNBLOCKED: a preamble emitted OUTSIDE `demo_block` gives match_ratio 1.000 (min AND mean) at ALL FOUR doses**, pool 30 → 160, with `demo_block` byte-unchanged and `main` still regenerating byte-identically. Demonstration-specificity is testable at n=4 and n=8 for the first time in the phase | **R-49**; supersedes the failed `main_longctx` approach | **R-49** |
| ⛔ **THE LONG-CONTEXT FIX FAILED: `filler_near` grows the DEMONSTRATION BLOCK (638→1644 chars at n=8) while the drawable outside stays at 90 chars on both banks.** Strictly worse. A working version must emit context OUTSIDE `demo_block`, which changes a field every bank and arm joins on — not a preset | **R-46**; `control_feasibility.py` also disagrees with ground truth and is quarantined | **R-46** |
| ⛔ **GATE FAILED / BRANCH STOPPED: demonstration-specificity is NOT CONSTRUCTIBLE on this bank.** Strict control feasible at **n_examples=1 only** (40/40), where the baseline is **2 attacks in 40 rows**; n=2 is 35/40 and rescoping to feasible rows is forbidden because demo length IS the dose. Needs a longer-context bank, a design change not an analysis one | jobs 780297-780299 all refused before generating | **R-25** |
| ⛔ **DEMONSTRATION-SPECIFICITY IS UNTESTED WHERE THE EFFECT LIVES.** The count-matched non-demo control has `match_ratio` **1.0 at n_examples 1-2** but **0.0 at 4 and 8** — the unprotected pool is empty once the demo block exceeds it. The arm refused before generating rather than under-matching silently | strict control runs at n=1,2 only; capped control read one-sided | **R-24**, **PR-10** |
| 🔴🔴🔴 **REFUTED: refusal restoration is NOT the route to attack removal.** Llama n=4: refusal rise **+0.2250 vs −0.0500 / −0.0500**, ΔASR **−0.1750 / −0.1750 / −0.1750 — identical**. Qwen3 n=8: the +0.2000-refusal arm removes **LESS** (−0.1500 vs −0.2000, gap clears margin). `demo_processing_only` restores refusal AND removes attack; the second is not carried by the first | dose-matched, pre-registered as the story-changing outcome in **PR-9** before reading | **R-23 / C-12** |
| ⚖️ **DOSE-RESPONSE: CONFIRMED ON LLAMA, REFUTED ON QWEN3.** Llama rise **+0.0000 / +0.0750 / +0.2250 / +0.3500** across n_examples 1/2/4/8, monotone, endpoint 6.7x margin, and **exactly zero at n=1**; Qwen3 non-monotone with endpoint **+0.0250, within margin**. Mechanism is single-model | controls flat at/below zero on both models, so not prompt length | **R-22**, **PR-8** |
| 🏆 **PR-7 OUTCOME A: 0 degenerate rows in 165 killed attacks across 8 cells, `frac_scorable`=1.000 everywhere.** The zero-refusal arms kill by COHERENT NON-COMPLIANCE; mutation-verified detector; worst real row 0.640 vs a 0.45 threshold | the R-20 caveat against my own headline does not bite; leg (b) stands | **R-21** |
| ⚖️ **SIZE-MATCHED: identity, not count — but not identity ALONE.** At 24 positions each, a DEMO patch removes 4 refusal rows and restores **no** attack, while a QUERY patch removes **13** and restores attack (+0.0500). R-39's contrast survives size-matching. But 24 of ~114 demo positions buys only **36.4%** of the full effect, so magnitude scales with count too | **PR-18's outcomes A and C overlapped and both fired — reported as both, defect owned** | **R-40** |
| ⚖️ **LOCALISATION + A LIMIT ON IT: the attack damage is reachable from the QUERY span (+0.0563, clears margin; control inert) but NOT from the demonstration positions.** However the query patch also removes **96.2%** of the refusal rise, so it is **not selective** — this is a **SINGLE dissociation, not a double one**, and the "separate loci" reading is excluded | ASR recovery only **37.5%**, still above margin from clean: partial, not restoration | **R-39** |
| 🏆🏆🏆 **COMPLETE 2x2 — MODEL FAMILY x DEMONSTRATION POOL, 4/4.** Refusal rows removed **18 / 17 / 12 / 18** against an **8.3-row margin** (**2.16x / 2.04x / 1.44x / 2.16x**); as percentages of the rise that is 69.2 / 81.0 / 92.3 / 58.1%, **but see DR-5: the percentages are inverted relative to the evidence** because a near-zero clean baseline inflates them. Control **exactly 0 rows in all four** | PR-14 both conditions HOLD, committed before the jobs existed | **R-36** |
| ⛔ **WITHDRAWN BEFORE IT WAS EVER A CLAIM: the Qwen3 ASR rescue FAILED its confirmatory test on an independent pool** (+0.0625 pool A vs **+0.0437 pool B**, needed >0.0521 — missed by ~1.3 rows). Not promoted, not rescued, no margin moved | **R-37**; the pre-registration is why this is a non-event rather than a retraction | **R-37** |
| ⚠️ **superseded by R-37 — on Qwen3 the same patch also appeared to restore the ATTACK** (knockout 0.0437 → 0.1062 vs clean 0.1313; Outcome-A shape) where Llama gave Outcome C. PR-14 pre-committed that the ASR column does not count here. Needs its own pre-registration + replication | the phase's causal picture may be model-dependent on ASR while model-independent on refusal | **R-36** |
| 🏆🏆🏆 **CAUSAL DISSOCIATION: one patch gives back the REFUSAL but not the ATTACK.** Handing clean demo-position activations back at L14 removes **69.2%** of the knockout's refusal rise (35→17 rows, >2x margin) while ASR stays **within margin of knockout-only** (recovers 16.7%). Below-band L5 control moves refusal by **exactly 0.0000** | PR-13 Outcome C on ASR; precondition `fired` 320/320; committed before the jobs existed | **R-35** |
| ⛔ **LAYER-SPECIFICITY DOES NOT REPLICATE — the rescue effect is NOT specific to the top of the band.** Llama mid-band (L10) restores refusal **−0.0688, p=0.019**, clearing the margin, where Qwen3 mid-band (L12) gave **−0.0375, p=0.21**. PR-28's condition 2 fails. Separation holds in both (0.0875 p=0.00052; 0.0562 p=0.0117) but all three conditions were required | **C9/C11/C12 do not get their specificity leg back** (C-20 removed it; their primary effects never rested on it). R-70's L12/L17 observation withdrawn as a candidate claim. **No layer sweep run — that would be rescuing a failed gate** | **R-71** (PR-28) |
| ✅ **REFUSAL METRICS HAVE NO MEASURABLE JUDGE OR TRUNCATION NOISE — only population sampling.** `kw_refusal` disagrees on **0/160** rows of byte-identical text (DR-10), and between a 192- and a 640-token cap **81/96 completions changed while 0 refusal decisions moved** (R-75). Every claim in this branch is a refusal claim | So C1 (4 settings), R-70 and R-71 need **no per-claim truncation check**; ASR keeps both caveats. ⚠ cap-invariance measured on **one bank, one model** — strong evidence, not proof | **DR-11**, **R-75**, **DR-10** |
| ⚠️ **THE LLM JUDGE FLIPS 9/160 ROWS ON BYTE-IDENTICAL TEXT (0.0563), while `kw_refusal` flips 0/160.** Not threshold adjacency — only 6/160 rows are score-adjacent to the cut and **four flips swing 0.0 ↔ ≥0.5**. Per-dose churn is **2,3,1,3 rows per 40-row cell**, against C7 per-cell effects of **3-7 rows** | **Net** churn is 1 row so PR-3's margins stand and no number moves; but **no single 40-row cell is decisive alone** — C7 is carried by **three independent populations agreeing in sign at both doses** | **R-70**, **DR-10** |
| 🏆 **§20 Q7 ANSWERED: C11's refusal half and its dissociation REPLICATE on Qwen3-14B.** Query-span rescue at L17 moves refusal **−0.09375 (−15/160) (−15 rows, 71.4% of the knockout's rise)** while ASR moves **−0.0062 (−1 row, −7.7% recovery)**; dissociation **0.0875** vs a 0.0417 margin. Llama gave −0.1562 / 96.2%. **The ASR half DECLINES for power** (inside ±0.0521), per PR-27's rule — not refuted | judge 800 rows 0 nulls; all arms same bank + same session; layer-specificity read is **EXPLORATORY** (no criterion was pre-registered for L12) | **R-70** (PR-27) |
| ✅ **§20 Q3 rescue instrument VALIDATED end-to-end: identity control 8/8 byte-identical to the arm, while the clean-donor rescue differs on 8/8.** Identical where it must be, different where it must be | no rescue science yet; sweep gated on a pre-registration | **R-33** |
| 🏆🏆🏆 **C1 NOW HOLDS IN THREE INDEPENDENT SETTINGS — two model families and two demonstration pools sharing NO sentences.** `demoproc` refusal rise **+0.1625** (Llama/A), **+0.1312** (Qwen3/A), **+0.1938** (Llama/B); every other scope within margin in all three. §20 Q5 ANSWERED | PR-12 both conditions HOLD; committed before pool B existed | **R-29** |
| 🏆🏆🏆 **TWO MODELS, FOUR SCOPES, EIGHT CELLS: exactly ONE restores refusal — `demo_processing_only`.** Qwen3 rise **+0.1312** (2.5x margin) vs **−0.0125** for all three others; killed-by-refusal **40%** vs **0% / 0% / 0%**. On Qwen3 it does this with the SMALLEST ASR effect and a NULL sign test, both pre-committed as non-counting in **PR-6** before reading | PR-6 all three conditions HOLD; provenance 800/800 | **R-20** |
| 🏆🏆🏆 **THREE SCOPES REMOVE A STATISTICALLY INDISTINGUISHABLE AMOUNT OF ATTACK BY DIFFERENT ROUTES.** ASR gaps demoproc-vs-legacy **0.0250** and legacy-vs-respq **0.0188** are both INSIDE the pre-registered 0.0417 margin; the arms separate only on **refusal** — demoproc **14/25 (56%)** killed-by-refusal at rate **0.2188**, vs **0/24** and **0/24** at 0.0312 and 0.0125, baseline 0.0563 | k=10, n=160; refusal measured by deterministic `kw_refusal`, not the LLM judge | **R-19**, **C-11** |
| ⚠️ **WITHDRAWN: "response_query_only is a weak partial" (R-10, Outcome B).** At k=10 respq is **85%** of legacy, gap 0.0188, which PASSES the same pre-registered margin it failed at k=6 | partial non-replication, reported rather than resolved by picking a bank | **R-19** |
| 🏆🏆🏆 **BOTH MODELS, WITHIN-FAMILY: in 6/6 arm×model cells, binding loss carries NO positive information about attack death** — 3 flat, 3 pointing the wrong way | Qwen3 `demo_processing_only`: **0/10** killed lost binding vs **5/38** not-killed; `legacy` flattens 28/48 | **R-17** |
| 🏆🏆🏆 **WITHIN-FAMILY: the attack dies where the mapping survives.** `demo_processing_only` kills **7** attacks and loses binding on **0 of 48** families (rule-of-three ≤ 0.0625); `query_prefill_only` loses binding on **8/41** families whose attack survived and **0/7** of those it killed — **anti-associated** | 48 families, each one behavioural row + one probe row sharing a byte-identical demo block | **R-16** |
| 🏆🏆🏆 **THE BINDING SURVIVES THE INTERVENTION THAT KILLS THE BEHAVIOUR.** `demo_processing_only` removes ~75 % of attack success (Δ −0.1250 Llama / −0.1562 Qwen3) yet takes binding accuracy **0.8750 → 1.0000**, rescuing **all 6** failing rows (0 down / 6 up, McNemar p = 0.0312 **at its floor**), while the late control moves **0/0**. **Representation and behaviour are separable at the exact point the intervention works** | 5 arms × 48 forced-choice rows, Llama, option mass 0.37–0.60, `frac_rows_scope_live` 1.0 | **R-15** |
| ⚠ **…and across arms the two quantities move in OPPOSITE directions** | margin loss `legacy` −2.557, `qpre` −2.172, `demoproc` **−0.897** (smallest) — the arm that hurts behaviour most hurts the mapping least | **R-15** |
| 🏆🏆 **OUTCOME B REPLICATES ACROSS TWO MODEL FAMILIES.** Qwen3: `demoproc` **−0.1562** vs `respq` **−0.0729** (PR-5 cond. 1 holds by +0.0833); primary fails equivalence (gap 0.0937, respq = 43.8 % of legacy). **Neither response-side arm is DISTINGUISHABLE from its late-layer control** (`respq − late11` CI [−0.0572, +0.0572]) ⚠ *amended by C-9a: the +0.0000 is a balanced tie, NOT per-prompt identity — 88/96 same label, 4up/4down, 0/96 identical generations* | 8 arms, one pinned session, n=96, Qwen3 L7–17, baseline 0.1771 | **R-12**, amended **C-9** |
| ✅ **`demo_processing_only`'s effect is NOT refusal, NOT truncation, and NOT dose** | down-flips decompose 15 = 3 refused + 3 short + **12 neither** (Llama) and 17 = 4 + 4 + **12 neither** (Qwen3); non-refused Δ **−0.1200 / −0.1358**; it makes output **longer** (ratio 1.14) and still beats its control length-matched (**−0.1310 vs −0.0714**); Spearman(edits, Δ) = −0.40 / −0.30 | **C-9b**, **C-9** |
| ⚠ **`legacy_all_query`'s Qwen3 advantage IS length-carried** | median length ratio **0.6461**, 56/96 rows shortened ≥30 %, 13 of 17 down-flips length-collapsed; length-matched **−0.0750 vs control −0.0714** — it no longer beats its control | **C-9b** |
| ⛔ **At the bank's real unit (24 nested demonstration cells) the arm-vs-control contrast does not replicate** | **Llama `demoproc` p = 0.0063** (the phase's first sub-0.05 at a defensible unit); **Qwen3 p = 0.2188** for both `legacy` and `demoproc` | **C-9c** |
| ⛔ **EVERYTHING in Phase 1 is lexical G = 1** | one `codeword`, one `concept`, one `condition`, one `role_style` — n_distinct = 1 on all ten design fields across all 96 prompts and all 6 domains | **C-9d** |
| ⚠ **`query_prefill_only` is model-specific and non-specific**: Llama **+0.0625** (wrong way), Qwen3 **−0.0729** but **exactly equal to its late control** | PR-5 condition 3 fails; its meaning was fixed before the run | **R-12**, PR-5 |
| ✅ **The refusal signature is cross-model; the length collapse is not** | `demoproc` refuses 0.208 (Llama) / **0.156** (Qwen3) vs legacy 0.010 / 0.000; rows <200 chars 20 (Llama) vs **1** (Qwen3) | R-10, **R-12** |
| 🏆 **OUTCOME B: the causal path is NOT response-time retrieval.** Corrupting the demonstrations' own prefill encoding carries **92.3 %** of the legacy effect (Δ −0.1250 vs −0.1354); masking the response's access carries **46.2 %** (−0.0625); the primary comparison **fails equivalence** (gap 0.0729 > margin 0.0417). Masking the final query's prefill access moves ASR **the wrong way, +0.0625** | 8 arms, one pinned judging session, n=96, Llama L6–14; effect **survives** length conditioning (−0.1200 at T=200) | **R-10** |
| ⚠ **…and the winning arm suppresses through REFUSAL, not through losing the mapping** | `demo_processing_only` refusal **0.208** against `legacy` 0.010 and `response_query_only` 0.021 — 20× | **R-10** |
| ⛔ **No arm reaches significance at the pre-registered unit** | domain-clustered p = 0.3750 / **0.1250 at floor** / 0.6250 / 1.0000; attainable floor 0.0625–0.1250, so magnitude cannot enter the p | **R-10**, predicted by **PR-3** |
| ✅ **Judge provenance is closed for the first time** | `judge_model_used = openai/gpt-4o-mini` on **768/768** rows, pre-flight canary matched the pinned model on every arm | R-10 |
| **The demonstration-attention knockout suppresses the doublespeak attack — DIRECTION, on the bomb corpus** | ⚠ **AMENDED by R-2.** The pooled 113 / 30 (p = 1.577e-12) is **one demonstration corpus**: bomb **81/11 p = 2.50e-14**, knife **15/7 p = 0.134**, gun **17/12 p = 0.458**; **drop bomb → 32/19, p = 0.092**. The 143 comparisons come from **67 distinct prompt_ids**. Replicates on the high-headroom bank of **both** models (**−0.1771** Llama, **−0.2083** Qwen3); every arm verified live; **no fitted direction, so no dose confound is possible** | R-R, R-T, R-AB, R-AY; **amended R-2** |
| ⚠ **…and the binding constraint is the number of DOMAINS, not banks/pools/models** | domain marginal k=6: `game_manual` −0.2562, `news_report` −0.0938, `city_bridge` −0.0875, `instructional` −0.0750, `farm_storage` −0.0063, `lab_safety` +0.0000; mean −0.0865, sd 0.0927, d = 0.933, **CI upper +0.0108 → includes zero**. Projection at fixed mean/sd: **8 domains → −0.0090 (excludes zero)**, 10 → −0.0202, 12 → −0.0276 | **prev-R-BE** (`7838dcd2`), inherited; see **D-4** |
| **The both-EOS control is not a 10-population control** | reproduces at 30/1 (p = 2.98e-08) but **5 of 10 populations contribute zero both-EOS discordant rows** | **R-2** |
| ⚠ **…but NO calibrated cluster test of MAGNITUDE excludes zero** | `pool × domain` k=18 was a **crossed 3×6 table on one shared 96-prompt set**; both marginals include zero (**k=3 pools [−0.3043, +0.1516]**, **k=6 domains [−0.1649, +0.0121]**); crossed random-effects CI **[−0.2796, +0.1268]** at df 2.53 | **C-18 / REVIEW-8** — *R-BD RETRACTED* |
| Retrieval and refusal are **independent channels** on Llama | knockout Δ = −0.1771 with refusal intact **and** with refusal removed; refusal removal alone includes zero | R-T ⚠ aggregate-level only (see DEAD row on "the same 17 prompts") |
| **The mechanism is layer-redundant** | all 40 heads of Qwen3 L8 = **+0.0104**; ≥8 contiguous layers needed for a large effect | R-AM, R-AQ (D-12) |
| **A concept axis `N` is invariant across 4 codewords at the split-half ceiling** | cos **0.984–0.989** vs an isotropic null with \|max\| **0.0569** | R-AE P4, survives C-7 |
| **Concept identity is a dominant plane with real third-direction structure** | PC3 **0.164–0.249** vs a pre-registered isotropic null of **[0.3170, 0.3297]**; replicated on two codewords | R-AX, R-BC |
| **Codeword identity is a (K−1)-dim subspace, not an axis** | four distinct reproducible `u_c`, split-half 0.985–0.997 | R-AE Test 2, C-4 |
| **`d_surface` fails specificity at matched dose** | at a real dose *below* the inert concept arm the codeword arm does nothing (+0.0104, p = 1.0000) | R-AH |
| **The retrieval scalar fails prediction and transfer** | vanishes within `n_examples` strata (3 of 4 exactly 0.0000); band-mean **anti-predicts** on Qwen3 | R-AJ, R-AK |
| **Attackability is a (bank × model) property** | two models on the identical bank share **1 of 9** attackable prompts | R-AU |

### ⛔ DEAD — do not quote these

| retracted claim | why | superseded by |
|---|---|---|
| **R-BD** "the calibrated CI excludes zero at k=18" (Δ −0.0764, [−0.1459, −0.0069]) | crossed 3×6 table on one shared prompt set; **62.1 %** of the spread is two main effects counted 3× and 6× over | **C-18** |
| **R-BA** (p = 0.0156 "weights by evidence", "robust to any drop") | p is sign-only; LOO provably cannot fail; fails leave-one-**model**-out (0.109) | C-16, C-17 |
| **R-AR** `p = 2.44e-04` and its bank×domain clustering | banks share only 2 demo pools → bootstrap miscalibration → model non-independence | C-11 → C-13 → C-14 → C-17 |
| **R-AV / R-AW** ("CI excludes zero at EVERY unit"; "every arm excludes zero, every control includes it") | percentile bootstrap ~30 % too narrow at small k; tail counts are the arithmetic floor `(n_zero/k)^k` | C-14 |
| **R-AG** "at matched dose, identity decides behaviour" | dose measured in a space the hook does not act in (6.60× real gap) | C-6 |
| **R-AN / R-AO / R-AP** layer laws | fitted to 1–3 prompt differences smaller than the measurement's own reproducibility | C-10 |
| R-AK "attention mass irrelevant at **any** granularity" | at head granularity the causal band wins on Qwen3 | C-8 |
| "the codeword axis `W`" / "the concept axis `N`" **as axes** | both are chords of subspaces | C-4, R-AX |
| Qwen3 "**hard** `in_subspace_orth` control" | 24.79× weaker; a dose-matched orthogonal control at L11 cannot exist | C-3 |
| **`C_all` (all-layers knockout) as "100 % suppression"** | degenerate — 24 (Llama) / 10 (Qwen3) distinct completions of 96 | R-AB, S8 |
| **The old `--demo-deleted` arm as a population ceiling** | the 96-row arm is **one prompt**, 1 distinct generation | REVIEW-2 M1 |
| **`goal_topicality` as evidence the model lost the mapping** | reads 0.0000 on the baseline too, by construction on a doublespeak bank | R-R |
| **"the knockout removes the same ~17 prompts regardless of refusal state"** | nets are −17/96 in both, but **23 vs 19** prompts cross the threshold and the down-sets overlap in only **7** | Part-II audit §11.1 defect 3 |
| **`uniq_frac` as "distinct completions"** | it is distinct completion **lengths**; by text Llama A and C_band are **96/96** unique | Part-II audit §11.1 defect 4 |

### 🔬 IN FLIGHT

*(none from this phase yet — see §B3 for the Phase-0 board)*

---

# PART A — THE PLAN *(stable; do not rewrite as results arrive)*

## 0. CURRENT STATE — TREAT THIS AS THE STARTING TRUTH

We continue from branch `behavioral-causality-sprint`. The plan as handed over named `8c83c8f3` as the
last audited state; **HEAD had already moved three commits past it when this file was opened**, and the
third of those commits **retracts the headline that `8c83c8f3` published**. Do not hard-reset. The
starting truth below is stated against `059e819f`.

**Reading order:** (1) `reports/SPRINT_SUMMARY_2026-08-23_TO_08-24_PART_II.md`;
(2) `external_md/BOOMBNESS_DSURFACE_NEXT_PHASE_PLAN_AND_PROGRESS.md`, especially its LIVE CLAIMS
LEDGER; (3) `reports/SPRINT_SUMMARY_2026-08-16_TO_08-26.md`;
(4) `reports/boombness_objective_sprint_report.md`; (5) the existing causal-intervention code
(`doublespeak_causality/pair_common.py`, `src/boombness/score_behavior.py`,
`src/boombness/surgical_knockout.py`); (6) `external_repos/interp-jailbreak` (Matan/Mor), reusing its
surgical patching / knockout methodology rather than reinventing infrastructure.

### What is closed

**`d_surface` is not our attack objective.** It is a real and highly reproducible representational
object, but there is **no demonstrated direction-specific causal role in jailbreak behaviour**. Its
apparent behavioural effects were repeatedly explained by **dose** or **output collapse**. The
crossed-bank repair gave the first genuinely dose-matched test and it was **negative**.
→ *Do not spend this sprint trying to rescue `d_surface`.*

**The attention-mass / retrieval-strength scalar is closed as an objective.** It is measurable, but
much of its apparent predictive power was `n_examples`; it does not track causal importance
consistently across models; on Qwen3 the relation **reverses**; and the strongest-attending single head
is causally **dispensable**. → *Do not build GCG/MAC around attention mass.*

**Fine-grained layer localisation is closed for now.** Differences between short sub-bands are smaller
than the experiment's own session-to-session reproducibility. → *No new large head sweep and no new
"layer law" unless a new experiment first provides a reason to reopen the question.*

### What survived

The strongest surviving result is the **demonstration-attention intervention**. Masking attention to
the demonstration block across a mid-stack band substantially suppresses the Doublespeak attack on both
models: **Llama-3.1-8B-Instruct ≈ −0.1771**, **Qwen3-14B ≈ −0.1667** (−0.2083 on the shared
high-headroom bank). The effect replicates across two model families; is much larger in the causal
mid-stack band than in the matched late-layer control; scales with demonstration count; is not explained
by the refusal channel on Llama; is distributed/redundant rather than carried by one head; and **fits no
direction, so the old direction-dose confound does not apply**.

**⚠ Correction to the plan's own statement of the magnitude claim.** The plan as handed over cites the
Phase-10 analysis — 3 pools, 5 banks, 2 models, 10 populations, `pool × domain` k=18, mean Δ ≈ −0.0764,
CI95 ≈ [−0.1459, −0.0069]. **That result (R-BD) was retracted by C-18 at 23:52 on 2026-08-24**, before
this phase opened. All ten populations use the **identical 96 `prompt_id`s**, so the 18 "clusters" are a
fully crossed 3 × 6 table in which **62.1 % of the variance is two main effects counted 3× and 6× over**;
both marginals include zero (k=3 pools [−0.3043, +0.1516]; k=6 domains [−0.1649, +0.0121]) and only
their product excludes it. **The correct position is C-17's:** *the direction is well supported;
no calibrated cluster test of magnitude excludes zero.* The result is also still materially stronger on
Qwen3 than on Llama — **Llama alone remains ≈ p = 0.131**, and under C-18's leave-one-out sweep **every
single drop kills the exclusion**.

**This does not weaken the case for the plan; it strengthens it.** The plan's own priority — isolate
*what computation the knockout destroys* — does not depend on the magnitude claim, and Phase 4 below is
now a genuinely open confirmatory question rather than a formality.

### The key unresolved issue

The current knockout has **not established exactly what computation is being destroyed**. The present
attention knockout can affect more than generated response tokens: depending on the query row during
prefill, it can also interfere with the **demonstrations' own processing**
(`lo = max(0, kp − past)` blocks each demonstration token from attending to itself and to earlier
demonstration tokens — recorded as caveat **S8** in the previous phase). So the wording *"generated
answer tokens need to retrieve information from the demonstrations"* is **stronger than what has been
isolated**.

> **The highest-priority experiment of this sprint is to separate response-query retrieval from
> demonstration encoding / prefill corruption.** This is more important than another layer/head sweep.

### The larger scientific goal

The project currently has: *representation is real*; *behaviour is causally attackable*; **but
representation and behaviour still do not meet.** This sprint tests a stronger causal chain:

```text
demonstration block
    ↓
response-time retrieval
    ↓
semantic codeword binding / remapping
    ↓
distributed internal state
    ↓
behavioral compliance
```

The goal is **not** to force this chain to be true. It is to test it hard enough that, whether it
survives or fails, we learn what the mechanism actually is.

---

## 1. NON-NEGOTIABLE WORKING RULES

### 1.1 Scientific rules

**Never interpret an intervention before proving it fired.** Every new intervention must carry explicit
liveness instrumentation recording at minimum: number/fraction of rows where the intervention was live;
prefill forwards; decode forwards; prefill edits; decode edits; number of keys actually masked; query
positions affected; layers affected; heads affected; intended versus resolved spans. **Any full
experiment with liveness below the pre-registered threshold is VOID** — do not "interpret with a caveat".

**Pre-register before the expensive result exists.** For each major experiment, write down first:
(1) primary estimand, (2) primary comparison, (3) unit of independence, (4) expected outcomes,
(5) what each outcome would mean, (6) falsifier, (7) stopping rule, (8) which secondary analyses are
allowed. Do not add the interpretation after seeing the number, and **if an interim result looks
favourable, do not compute an unregistered favourable subset.**

**Null-model-first geometry.** For every geometric claim: define the null, simulate or derive it, save
the null artifact, and only then inspect the observed geometry. Do not call a structure interesting
because it visually looks regular.

**Measurement reproducibility before structure fitting.** If an effect differs by only a few prompts,
first repeat the exact same arm in a second judging session. Do not fit laws to differences smaller
than the measurement's own reproducibility.

**Distinguish effect size from p-value floors.** With small cluster counts a sign-flip p may be pinned
at its arithmetic minimum. Always report effect magnitude, number of informative clusters, attainable
p-floor, and a calibrated interval where appropriate. Run the "destroy magnitudes, preserve signs"
diagnostic on any permutation statistic claiming to use magnitude; **if the p does not move, call it a
sign test.**

**Never treat bank, model and prompt count as independent when they are not.** The demonstration pool is
the meaningful independence axis; banks sharing a pool are not independent clusters; Llama and Qwen3 on
the same material are not automatically independent replicates. **And per C-18: a crossed table over two
shared design factors is not k = product-of-levels.** Preserve the `pool × domain` logic only as a
*marginal* analysis unless a new design creates a genuinely different unit.

**No per-prompt causal stories from unstable judge labels.** Identical completions can cross the 0.5
StrongReject threshold on re-judging (measured: same generations, two sessions, same binary label on
only **78/96** rows). Aggregate rates and paired aggregate differences are usable; per-prompt
"this exact prompt was rescued" stories require much stronger evidence. **Do not say two interventions
affect "the same prompts" merely because their net deltas match.**

### 1.2 Coding rules

Reuse existing code; prefer a small additive modification to the boombness / causality framework over
new machinery, and reuse `external_repos/interp-jailbreak` where it provides better patching practice.
**Do not rewrite old intervention classes whose semantics are needed to reproduce committed artifacts —
add new classes/modes instead.** Every important bug fix ships with a regression test that demonstrably
fails under the pre-fix behaviour; mutation-test critical guards where practical. **Do not duplicate
formulas inside tests** — import and test the real implementation.

### 1.3 Testing rules

Environment: `/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`. Login-shell
`python` has no torch; its failures are not repo failures. At the start run `check_all.py` and the full
`pytest tests/`. The inherited state — `check_all` green, **721 passed / 18 failed / 7 skipped** — is
**not** an acceptable "all green": fix or explicitly classify the 18 before building a large new stack,
and **take the 12 artifact-regeneration failures seriously** rather than dismissing them as environment
noise. For commits: always `check_all.py`, always the science-critical fast subset, the full relevant
suite before every milestone and during the 4-hour reviews. **Do not use `--no-verify`.**

### 1.4 Git rules

This branch has had an unexplained concurrent writer. Before every commit run `git status`,
`git log -n 5 --oneline`, `git diff`. **Stage explicit paths; never `git add -A`.** Do not overwrite
another session's work; if HEAD moves unexpectedly, inspect and reconcile before continuing. Commit and
push after meaningful progress — logical milestones, not one giant commit at the end.

### 1.5 Artifact rules

**No important number may exist only in markdown.** For every result save: producing script, compact
JSON artifact, exact input/run paths, model, bank, pool, intervention spec, judge config, estimator,
cluster definition, seed, git SHA, timestamp, DONE marker. `outputs/` is gitignored, so **also create a
tracked compact result manifest for every paper-level result** — small JSON summaries, hashes, producing
paths and commands, never huge tensors. This explicitly fixes the situation where **R-W and R-AC can
only be reconstructed by reverse-engineering prose.**

### 1.6 SLURM rules

GPU-heavy work runs through SLURM, never the login node. Use the known-working account/partition; do not
repeatedly probe inaccessible partitions. Keep **≈ 6 or fewer independent GPU runs in flight**. Use CPU
nodes for statistical analysis, artifact audits, prompt generation, API judging, null simulations and
report generation. Parallelise genuinely independent work; do not parallelise where a later arm depends
on an earlier gate. **Record every job id and final status; FAILED/CANCELLED jobs stay visible in this
log.**

### 1.7 Dataset / split rules

Maintain family-disjoint dev/heldout splits; never reintroduce the sibling-family leakage that
invalidated G2. Do not optimise on heldout prompts. For every new bank audit explicitly: rows, family
ids, split overlap, demonstration-pool hash, prompt ids, template identities, token alignment, codeword
occurrence alignment, demo-span alignment, grammar, tokenizer behaviour on **both** models. Use at least
the existing scale; do not interpret tiny samples as final results.

---

## 2. PHASE 0 — REPAIR THE EVIDENCE PIPELINE BEFORE NEW SCIENCE

### 2.1 Reproduce the current headline

Recompute the current cross-bank result from its **raw** artifacts via an **independent** analysis path
— not by calling the existing summary writer. Confirm population membership, pool hashes, the cluster
counts, the aggregation, model-specific values, calibrated intervals, the sign-flip statistic, the
count-permutation statistic and the both-EOS control. **Given C-18, the object to reproduce is the
C-17/C-18 position** (direction supported; marginals include zero), not R-BD. Save the re-derivation as
a tracked compact artifact.

### 2.2 Fix known live artifact defects

*(Several of these were fixed by the peer session's C-18 code closure at 00:12 — verify each before
re-fixing, and do not duplicate.)*

* **Crossbank summary overwrite** — `summary.json` keys omitted the model, so Llama silently overwrote
  Qwen3. Schema must carry an explicit model dimension. Regression test with two models and
  deliberately different values.
* **`n_independent_pools`** — must count distinct demonstration-pool identities/hashes, not bank names.
  Test with several banks sharing one pool.
* **Strict bank generation** — validation must happen **before** the bank is available as an output.
  `--strict` must not leave a violating bank consumable merely because the file exists: write to a
  temporary path and rename only after validation. Regression test reproducing the `arrow` failure.
* **Misleading metric names** — no more `uniq_frac` for distinct completion *lengths*, `delta_pooled`
  for a mean-*score* delta, bare `dose` without naming the norm/variance/residual quantity, or
  `spearman` for Pearson-on-log2. Keep backward compatibility for old artifacts; **new artifacts must be
  unambiguous.**
* **Judge provenance** — build a mode where the judge model is selected and pre-flighted **before** the
  session, frozen for it, and persisted along with the raw judge response, prompt/completion hashes;
  where the same completion is not needlessly re-judged; and where a partial backend failure cannot
  silently turn one session into a mixed-model judge. **Do not rewrite historical artifacts.**
* **Incomplete run directories** — identify the three `crossbank_knockout_test` dirs without
  `DONE.json`; either complete them or mark them excluded in a **machine-readable** manifest so no
  glob-based analysis ingests them.

### 2.3 Fix the real failing tests

Run the full suite in the correct environment and separate genuine repo failures from
environment-dependent ones. **If a committed recipe no longer reproduces its committed artifact, fix the
recipe or explicitly version the artifact. Do not weaken tests to obtain green.**

### 🚦 PHASE-0 EXIT GATE

No large GPU matrix until: `check_all.py` passes; science-critical tests pass; genuine full-suite
failures are repaired or classified; crossbank summary overwrite fixed; pool counting fixed; strict
generation safe; judge backend provenance fixed for new runs; and the current headline independently
reproduces. **Commit and push this state.**

---

## 3. PHASE 1 — ISOLATE WHAT THE DEMONSTRATION KNOCKOUT IS ACTUALLY DOING

**Core question.** Does the causal effect come from (1) generated response tokens retrieving from the
demonstrations, (2) the final query representation retrieving during prefill, (3) corruption of the
demonstrations' own representations, or (4) some combination?

### 3.1 Scoped attention-knockout semantics

Add an **additive** implementation that independently controls:

| mode | prefill behaviour | decode behaviour |
|---|---|---|
| **`query_prefill_only`** | only the final user/query span is blocked from attending to demo keys; demo tokens process normally | unmodified |
| **`decode_only`** | unmodified | generated-token query rows blocked from demo keys |
| **`response_query_only`** | final query span blocked | all generated query rows blocked — demo-token processing untouched. **The cleanest test of "the response computation needs access to the demonstrations."** |
| **`demo_processing_only`** | query rows *inside* the demonstration block blocked from demo keys; final-query/decode access left intact where possible | unmodified |
| **`legacy_all_query`** | the existing `AllQueryAttentionKnockout` semantics, unchanged | unchanged — the bridge to the previous result |

**Document explicitly:** `decode_only` **cannot** affect the logits used to sample the first generated
token if those logits come from the final prefill query state.

### 3.2 Required synthetic tests

Small deterministic synthetic-attention tests proving, per mode: exactly which query rows are edited;
exactly which key positions; prefill behaviour; cached-decode behaviour; first-token behaviour;
multi-token behaviour; different prompt and demo lengths; **no `kp`/`past` coordinate confusion**; no
modification outside selected layers; none outside selected heads. **Mutation-test the span resolver and
the decode liveness condition — the old failure mode must turn the regression test red.**

### 3.3 First smoke

≈ 8 rows per model. Do not judge scientific effect. Check: 100 % of intended rows hit the hook; expected
prefill/decode counters; generations actually change; no crashes; no pathological collapse; **no
all-layer experiment.** If the hook does not fire exactly as designed, fix it before continuing.

---

## 4. PHASE 1 FULL EXPERIMENT — SAME-SESSION DECOMPOSITION

Canonical **96-row** behavioural population, both models, the already-supported causal bands
(**Llama L6–14**, **Qwen3 depth-matched L7–17**). **Do not retune these based on new outcomes.**

**Arms (minimum):** `A_baseline` · `C_legacy_full_scope` · `C_response_query_only` ·
`C_query_prefill_only` · `C_decode_only` · `C_demo_processing_only` · `D_response_query_late_control`.

Plus **same-band non-demo-key controls**: mask approximately the same number of key positions outside
the demo block, using **≥ 3 seeded deterministic draws** rather than one random lottery; protect
special/query-critical regions from accidental masking; **persist the exact positions used per row.**

**4.1 Judge all directly comparable arms in ONE session** with one fixed, pre-flighted backend. Do not
compare a new arm against an arm judged in an old session. Report **mean StrongReject score** and
**binary ASR@0.5**; pre-register 0.25 / 0.50 / 0.75 sensitivity as secondary.

**4.2 Generation-health metrics per arm:** median/mean characters; truncation rate; EOS termination
rate; refusal rate; **number of unique completion texts**; **number of distinct completion lengths as a
separately named metric**; empty/near-empty fraction; generation-change rate vs baseline. **A reduction
in judged ASR is not behavioural suppression if it is another output-length collapse.**

**4.3 Pre-register interpretation categories** with an equivalence margin fixed *before* judging, using
the known within-session reproducibility (≈ 2–3 prompts of 96) as the reference:

* **Outcome A** — `response_query_only` ≈ legacy while `demo_processing_only` is weak → strong evidence
  the causal path is **response/query access to demonstration information**.
* **Outcome B** — `demo_processing_only` carries most of it → **retract/reframe** the "generated answer
  retrieval" wording; the result becomes *disrupting the demonstrations' internal representation
  suppresses the attack*. Still scientifically interesting.
* **Outcome C** — `query_prefill_only` dominates, `decode_only` small → the retrieval event occurs
  largely while constructing the final query state before generation.
* **Outcome D** — `decode_only` remains large → genuinely ongoing retrieval during autoregressive
  generation.
* **Outcome E** — legacy strong but **every** cleanly scoped arm weak → the legacy effect depends on
  interacting disruptions across prompt and response computation. **State that directly; do not average
  the scoped arms into a preferred story.**

---

## 5. PHASE 2 — BRIDGE THE BEHAVIOURAL RESULT TO SEMANTIC BINDING

The causal result shows behaviour changes when demo attention is blocked. It does **not** show what
semantic information was lost. `goal_topicality` is invalid here (successful Doublespeak outputs keep
speaking in the codeword and never use the target word) — **do not reuse it as the primary instrument.**

**5.1 Matched semantic binding probe.** For every behavioural family, a probe using the **same
demonstration block and same mapping**, e.g. *"In the code used above, what does `<codeword>` mean?
Answer with one word."* Measure recovery of the intended mapped concept with deterministic/model-native
measurements: exact one-word accuracy; probability/logit margin of the intended concept against
appropriate alternatives; forced-choice accuracy. **Do not fit a new arbitrary hidden-state direction
for this primary probe** — use the observable mapping output first.

**5.2 Run the causal intervention on the probe:** baseline · validated `response_query_only` ·
late-layer matched control · same-band non-demo controls, on the same families.
*Does the intervention that suppresses behavioural attack success also destroy recovery of the
codeword→concept mapping?* **This is the first direct bridge we need.**

**5.3 Cross-condition specificity** across the 2×2 conditions (A natural doublespeak · B benign literal ·
C direct harmful · E concept in benign context): is semantic mapping selectively affected where
demonstrations matter? does general benign instruction-following collapse? does direct-harmful
refusal/compliance change? is the intervention simply damaging generation? **Essential, because the
late-layer control alone does not rule out "masking a large prompt region mid-model generically hurts
in-context computation."**

---

## 6. PHASE 2B — CHARACTERISE WHAT THE SUPPRESSED COMPLETIONS BECOME

Build a **completion phenotype instrument**; do not use it as the primary causal estimator until its
reliability is measured. Mutually exclusive categories: (1) mapped/codeword compliance; (2) literal
codeword interpretation; (3) explicit refusal/safety response; (4) garbled/incomplete/truncated
non-answer; (5) other coherent response.

**Blind the evaluator to the arm.** Persist evaluator backend, prompt/version, raw output, parsed
category, completion hash. Use ≥ 2 independent views where practical (structured semantic classifier;
deterministic lexical/termination/refusal metrics) and **measure agreement — do not hide disagreement.**

> **When the attack disappears, did the model lose the mapping, refuse, become literal, or simply
> destabilise?** This is currently unknown and should become known.

---

## 7. PHASE 2C — REBUILD THE TEXT-DELETION CONTROL CORRECTLY

The old ceiling was invalid: the supposedly 96-row arm collapsed to essentially one prompt. Build a
**row-specific** demo-deletion transformation that preserves each row's query and row identity, removes
only the intended demonstrations, preserves the rest of the prompt structure, **verifies diversity by
text hash rather than length**, requires many distinct transformed prompts, saves transformed prompt
hashes, and **fails if accidental duplication exceeds a pre-registered threshold.**

Only after the transformation is proven correct, compare: demonstration text deletion · response-query
attention knockout · late control · same-band non-demo mask. **Do not call deletion a "ceiling" until it
is genuinely row-wise.**

---

## 8. PHASE 3 — CAUSAL RESCUE: CONNECT INTERNAL STATE TO BEHAVIOUR

Do not start by inventing another scalar. Ask the stronger question: **if the retrieval knockout
destroys a necessary internal state, can we restore that state and rescue the semantic mapping or
behaviour?** Use surgical activation-patching practice from the existing project and the local
`interp-jailbreak` code.

**8.1 Clean vs corrupted paired runs** on the exact same row (CLEAN = baseline, CORRUPTED = validated
retrieval knockout). Cache activations at: the final query token/span during prefill; band exit;
immediately after the causal band; attention output; residual stream. **Do not begin with hundreds of
heads — the previous data say the mechanism is distributed.**

**8.2 Full-state rescue first.** At a pre-registered boundary such as band exit, patch the CLEAN
residual state at the final query position into the CORRUPTED run. Primary target: **semantic binding
probe**. Secondary: behavioural generation. Controls: mismatched-family clean activation; clean
activation from a late/inert layer where dimensions allow; random-row activation; norm/energy-matched
perturbation. **A huge full-residual transplant is not direction specificity** — its only purpose is to
prove the lost causal information is recoverable at this state.

**8.3 Retrieval-effect subspace — only after full-state rescue succeeds.** Build the paired
intervention-effect matrix on **dev** only: `Δh = h_clean − h_knockout` at the pre-registered
state/layer. **Do not fit to StrongReject labels** — the basis comes from the causal perturbation, not
from attack outcomes. PCA/SVD or equivalent. Before looking at heldout behaviour, record the singular
spectrum, split-half stability, an isotropic/random-subspace null, and a **predeclared train-only
rank-selection rule** (not many ranks tried on heldout ASR).

**8.4 Low-rank add-back test** on heldout families: start from the knockout run, add back only the
clean-minus-knockout component **inside the learned subspace**, measure semantic recovery, then
behavioural rescue. Use **equal-rank random subspaces** and match the actual intervention energy.
Report semantic recovery, behavioural recovery, and **fraction of full-state rescue recovered**.

* **Low-rank rescue succeeds** → a major result: a compact state that is demonstration-induced, causally
  necessary and behaviourally relevant. *Only then* does it become a candidate optimization handle.
* **Full-state succeeds, low-rank fails** → also strong: the behaviourally necessary retrieval state is
  high-dimensional/distributed, consistent with the observed layer/head redundancy.
* **Even full-state fails** → the relevant information lives elsewhere, or generated-token dynamics
  dominate, or the intervention changes a distributed trajectory that cannot be repaired at one
  boundary. **Do not force a direction.**

---

## 9. PHASE 4 — ADD THE FOURTH INDEPENDENT DEMONSTRATION POOL

The magnitude claim is thin on Llama and — after C-18 — has **no surviving calibrated cluster test at
all**. The `club` corpus already exists and is audited. This is the obvious confirmatory increment, run
as a **frozen confirmatory analysis, not another adaptive statistics search**.

**9.1 Freeze the analysis before running club**, using only existing data: primary estimand; the
aggregation unit **(and, per C-18, whether it is a marginal or a crossed table)**; model handling; CI
procedure; count-permutation statistic; threshold; both-EOS control; leave-one-pool-out;
leave-one-model-out; model-specific analyses. **Persist this configuration before any club outcome is
inspected, and do not compute a favourable subset when the first arm arrives.**

**9.2 Run both existing club banks** rather than making new lexical material, using the validated scoped
intervention from Phase 1; optionally the legacy arm as a bridge, but it must not replace the cleaner
intervention. Both models if compute permits. **Two banks sharing the club pool do not create two
independent pools — the count becomes 4 pools, not 4 + banks.**

**9.3 Primary questions.** Does the pool-level interval remain below zero with a fourth pool? Does it
survive leave-one-pool-out? What happens to Llama alone? Does Qwen3 continue carrying it? Do
positive-delta churn cells continue to align with truncation/non-termination? Does the scoped
intervention produce a more stable result than the legacy one? **Accept the result even if Llama remains
null; do not keep adding pools until p crosses a preferred threshold.**

---

## 10. PHASE 5 — BUILD THE JOINT CROSSED BANK

The current crossed geometry pools **independently generated and fitted** banks, leaving a bank/pair
nuisance term. Build **one jointly generated crossed bank.**

**Factors.** Codewords: four existing audited consonant-initial codewords that avoid article-grammar
problems, tokenize cleanly and align on both tokenizers — **do not introduce a new codeword for
novelty.** Concepts: the established four — `bomb`, `knife`, `gun`, `club`. **Do not use `arrow`;
do not repeat the `a arrow` / `a apple` failure.**

**Joint design requirement.** All codeword × concept combinations generated from a **common
template/family universe**, with the base family identifiable independently of the lexical assignment,
and each pair's 2×2 cells preserved (natural doublespeak · benign literal · direct harmful · concept in
benign context). The purpose is to make codeword/concept variation the **controlled factor** rather than
*"which separately generated bank did this come from?"*

**Strict acceptance criteria before any geometry is fitted:** zero prompt-family violations; zero grammar
violations; zero ambiguous target occurrences; zero demo-span ambiguity; clean tokenizer audit;
base-family alignment across all pair combinations; family-disjoint train/dev/heldout; sufficient rows
per cell; model-specific tokenization report for **both** models. **The generator must abort before a
violating bank becomes available.**

---

## 11. PHASE 5B — REPLICATE THE GEOMETRY ON LLAMA *AND* QWEN3

The current decomposition is Llama-only. **11.1** Pre-register normalised-depth analysis layers — do not
select Qwen3 layers after seeing which look most similar; fit all layers if cheap but distinguish
pre-registered primary depths from exploratory plots. **11.2** Compute split-half ceilings first for
every factor/subspace (dev fit, heldout fit, similarity, null) — no cross-factor statement is meaningful
without the measurement ceiling. **11.3** Use a proper factor decomposition with **orthonormal bases**;
do not repeat tables that mix projection fractions, raw norms and nested terms and *look* like a variance
partition without being one; state whether terms are orthogonal, nested or overlapping, and **do not make
them sum to 1 unless they mathematically partition.**

**11.4 Main questions.** Is the concept representation codeword-invariant on the joint bank? Does the
four-concept representation remain plane-dominated with non-zero third-direction structure? Does Qwen3
show the same structure? Is the codeword side genuinely a (K−1)-dimensional factor subspace? Does the
interaction remain small under a joint design? At what depths does factor separation emerge? Isotropic
nulls fixed before observed structure is interpreted. **This can be a valuable representational result
even if it stays behaviourally non-causal — do not quietly reconnect it to ASR without a causal bridge.**

---

## 12. PHASE 6 — QWEN3 REPLICATION OF RETRIEVAL × REFUSAL

The Llama 2×2 suggested retrieval and refusal are separate channels; that has not been cleanly
replicated on Qwen3. **Do not reuse a Llama refusal direction in Qwen3.**

**12.1** Build/validate a Qwen3-specific refusal intervention with the existing refusal-direction
machinery. Choose the primary candidate layer(s) **before** evaluating the doublespeak interaction; a
depth-matched layer should be considered. The existing Qwen3 refusal directions at L20/L25/L28 are
secondary references — do not force them into an interaction merely because they exist. Validate on
heldout harmful/benign data: does projection actually change refusal behaviour? does it avoid
pathological benign degradation? does the intervention fire? is the effect measurable?

**12.2 Identifiability gate.** If refusal removal has essentially no measurable effect on the chosen
Qwen3 population, a retrieval × refusal interaction **is not identifiable there**. **Do not claim
"independence" from two inert cells** — record *refusal interaction unidentifiable on this population.*
If there is headroom, run one same-session 2×2 (baseline · retrieval knockout · refusal · both) using
the **validated scoped** retrieval intervention, comparing aggregate effects only.

---

## 13. PHASE 7 — OBJECTIVE REOPEN GATE

**There is currently no justified GCG/MAC objective. That is a scientific result, not an unfinished
task.** The track reopens only if a new candidate — most plausibly the Phase-3 retrieval-effect subspace
— passes all six gates:

* **O1 Measurement** — reproducible across split halves; not dominated by measurement noise; **not simply
  `n_examples`, completion length, or refusal score.**
* **O2 Prediction** — on heldout data predicts semantic mapping, behavioural vulnerability, or causal
  knockout sensitivity, **after conditioning on demonstration count, bank, domain and pool.**
* **O3 Causality** — a direct intervention on the candidate changes the relevant quantity, with
  energy/dose-matched controls; **random directions/subspaces must be allowed to fail.**
* **O4 Specificity** — beats matched random/equal-rank controls, **not merely by removing more residual
  energy.**
* **O5 Transfer** — the sign/role must be coherent on both models. The vector need not transfer across
  hidden dimensions, but the mechanism cannot mean *"ascend on Llama and descend on Qwen3."*
* **O6 Optimization direction** — a clear scalar loss whose causal meaning is supported, which does not
  reproduce length collapse, the refusal lottery, the attention-mass reversal, or dose-only behaviour.

---

## 14. ONLY IF ALL OBJECTIVE GATES PASS — GCG/MAC

If any gate fails, **Phase 7 remains BLOCKED and GCG/MAC is not implemented.** If all pass: reuse the
existing GCG/MAC implementation from the article/local repos; minimise new code; optimise only on
dev/train families; **freeze the suffix before heldout evaluation**; compare against the standard
GCG/MAC objective, a random equal-rank subspace, `d_surface`, attention mass and a refusal objective;
evaluate transfer across heldout families, codewords, concepts, pools and models where dimensionally
possible; record ASR, semantic mapping, refusal, generation length, truncation and objective value; and
**explicitly test whether optimization merely collapses generation.**

> The goal is to **discover** a mechanism-derived optimization target, not to manufacture one.
> *"The causal mechanism is distributed and does not admit a useful low-dimensional optimization
> handle"* is a valid and potentially stronger paper result.

---

## 15. LATER GENERALIZATION — ONLY AFTER THE MECHANISM IS CLEAN

**Third model family** — only if the repo already supports one with reasonable attack headroom; use a
headroom gate before interpreting a null; **do not tune the causal band by looking at ASR** — use
depth-normalised pre-registration. **Quantized variant** — if already supported, test whether the causal
retrieval effect survives quantization. Both are **secondary** generalization results.

---

## 16. THINGS NOT TO DO IN THIS SPRINT

Do not: rescue `d_surface` · call it "bombness" · build GCG from `d_surface` · build GCG from raw
attention mass · run another huge single-head sweep · infer a layer law from 1–3 prompt differences ·
treat all-layer knockout as clean evidence · use `C_all` as "100 % suppression" · use the old
text-deletion arm as a population ceiling · use `goal_topicality` as evidence the mapping was lost ·
use `arrow` · add new lexical concepts before exhausting the audited set · use a single random control
at large magnitude · call model/bank replicates independent when they share pools or prompts · report
uncalibrated small-k percentile bootstrap intervals as definitive · round a CI across zero · say "all
tests pass" when only `check_all.py` passes · persist a statistical function that is never called ·
leave a headline number only in markdown · interpret an intervention without liveness proof · hide
failed or cancelled jobs.

---

## 17. REVIEW PROTOCOL

Use subagents aggressively for independent tracks: intervention semantics + synthetic tests · statistics
audit · judge/provenance repair · prompt-bank validation · artifact/reproducibility audit · independent
adversarial reviewer. **Do not use multiple agents to change the same files without coordination.**

For each major result, run an adversarial reviewer instructed approximately:

> *Try to prove this claim wrong. Recompute it from the raw artifact. Check population identity,
> intervention liveness, model/pool independence, estimator definition, judge provenance, truncation,
> alternative controls, and whether the statistic is saturated or misnamed. Default to refuting the
> proposed interpretation.*

Do this **before** promoting a result to the LIVE CLAIMS LEDGER. If the reviewer overturns it: append a
correction, do not rewrite history, mark the previous claim superseded/retracted, update the ledger.

---

## 18. 30-MINUTE / 4-HOUR WORK LOOP

**Every ≈ 30 minutes:** inspect running jobs; inspect failed jobs; check whether a gate has resolved;
update this file; commit/push meaningful completed progress; queue only experiments still justified by
current evidence.

**Every ≈ 4 hours, a deeper code + output review:** inspect git diff/history · run `check_all.py` · run
the relevant/full test suite · inspect recent raw outputs manually · independently recompute current
headline numbers · check liveness fields · check pool/model/bank provenance · check for silent
overwrites · check judge-session consistency · check whether any claimed p is actually sign-only · check
truncation/EOS · check whether structure is being fitted below the reproducibility floor · update the
LIVE CLAIMS LEDGER · document corrections immediately. **Continue after the review; do not stop because
one experiment completed.**

---

## 19. REQUIRED FINAL DELIVERABLES

**A. Live research log** — this file, with the full chronological record.
**B. A clean sprint summary** — a new report covering only this phase, understandable with no session
context, structured like the Part-II summary: starting state · plan · exact experiments · where we won ·
where we failed · corrections · final claims · limitations · canonical artifacts · reproduction.
**C. Research handoff** — create/update `RESEARCH_HANDOFF.md`: exact current scientific truth ·
strongest result · retracted claims that must not be revived · open items · next decisive experiment ·
artifact paths · current HEAD.
**D. Paper-level claim table** — per surviving claim: claim text · model(s) · population · n ·
independence unit · effect size · interval/test · intervention · control · artifact · code · status
(exploratory / replicated / confirmatory / retracted / unresolved).
**E. Reproduction manifest** — every paper-level result has **one command/script path** that regenerates
its compact analysis artifact from raw data. **No important result should require reconstructing a
method from prose.**

---

## 20. WHAT SUCCESS LOOKS LIKE

Success is **not** "GCG works". This sprint succeeds if these are answered cleanly:

1. Is the demonstration-knockout effect genuinely caused by **response-query retrieval**, or partly by
   corrupting the demonstrations during prefill?
2. When the knockout suppresses the attack, **what changes** — codeword mapping, literal interpretation,
   refusal, generation quality, or something else?
3. Can the lost information be **causally rescued** by activation patching?
4. If full-state rescue works, is the behaviourally relevant information **low-rank or irreducibly
   distributed**?
5. Does the mechanism survive a **fourth independent demonstration pool**, especially on Llama?
6. Does the codeword/concept factorization replicate on **Qwen3** in a properly joint crossed design?
7. Does the Llama retrieval/refusal independence result replicate on Qwen3, or is it model-specific?
8. Only if the causal retrieval state becomes a stable, specific, transferable low-dimensional handle:
   can it become a legitimate GCG/MAC objective?

The ideal contribution is no longer *"we found a bombness direction"* — that hypothesis is closed. The
more interesting possible contribution is:

> **Doublespeak constructs a robust semantic remapping representation, but that representation alone is
> not behaviourally causal. The attack instead depends on a distributed, mid-stack demonstration-retrieval
> process. Removing response access to the demonstrations suppresses behaviour across model families; the
> next mechanistic question is whether the lost distributed state can be causally restored and compressed
> into a behaviourally meaningful representation.**

**Test that claim aggressively. Do not protect it.** If the response-only knockout fails, say so. If the
semantic binding survives while behaviour disappears, that is extremely important. If full-state patching
restores mapping but not behaviour, that is extremely important. If low-rank rescue fails, that is
extremely important. **The goal is to add a real causal result to the paper, not to preserve the story we
started with.**

---
---

# PART B — LIVE PROGRESS LOG *(append-oriented, newest first within each section)*

## B1. PRE-REGISTRATIONS

*(Each entry is fixed before the corresponding result exists and is never edited afterwards; a
superseded pre-registration gets a new entry that says so.)*

### 🔒 PR-5 (06:10) — **WHAT COUNTS AS QWEN3 REPLICATING OUTCOME B.** Fixed before the Qwen3 arms are submitted, and before any of them is judged.

R-10 ends with *"Outcome B is a claim about Llama-3.1-8B on this bank until it replicates."* **The
criteria for that are fixed here, in advance, because "did it replicate?" is the single easiest
question in this project to answer after the fact.**

**Design.** The identical 96-row population and the identical 8 arms, on `Qwen/Qwen3-14B`, at the
**depth-matched** band **L7–17** (11 of 40 blocks = 0.175–0.450 of depth, against Llama's 9 of 32 =
0.188–0.469) with late controls at **L25–39**. `--enable-thinking false`, as every prior Qwen3
boombness run. **The band is NOT retuned on the outcome** — it is the depth mapping the previous phase
already fixed, and prev-R-AB used exactly it.

⚠ **The depth match is not a count match, and the asymmetry is recorded now**: 11 blocks vs 9. Per
prev-Phase-4's own note this is *conservative for a positive result and permissive for a negative one*
— a wider band can only make a knockout stronger, so **if Qwen3 shows LESS suppression it cannot be
blamed on having cut too little.**

#### 📌 Outcome B replicates on Qwen3 if, and only if, ALL THREE hold

1. **`demo_processing_only` is the larger scoped arm**, i.e. `|Δ_demoproc| − |Δ_respq| > 0.0417`
   (PR-3's arm-vs-arm margin). *Direction of the inequality is what matters, not its size.*
2. **The primary comparison fails equivalence the same way**: `|Δ_respq − Δ_legacy| > 0.0417`, with
   `Δ_respq` recovering **less than half** of `Δ_legacy`.
3. **`query_prefill_only` does not suppress**: `Δ_qpre ≥ −0.0521` (PR-3's vs-baseline margin), i.e. it
   is inert or positive, never a real suppression.

#### 📌 And what each failure mode would mean — written now so it cannot be reframed later

* **All three hold** → Outcome B is a cross-model property of the mechanism, not of Llama. **That is
  the paper claim.**
* **(1) reverses** — `response_query_only` larger on Qwen3 → **the two models use different halves of
  the computation**, which is a genuine and publishable dissociation and *not* a failure. Report it as
  such; do **not** average the models.
* **(3) reverses** — `query_prefill_only` suppresses on Qwen3 → the Llama `+0.0625` is model-specific
  and must be reported as such rather than as a general finding about query-side access.
* **All arms weak on Qwen3** → check headroom FIRST. Qwen3's baseline on this bank was **0.1875**
  (prev-R-AA) so headroom exists, but if this session's baseline lands near the floor the arms are
  **uninterpretable, not null**, and the honest output is *"not measurable at this baseline"*.

#### 📌 Everything else is inherited unchanged

PR-3's margins and floors, PR-4's reporting rules (every ASR beside its truncation fraction and median
`n_chars`; the length-conditioned sweep; the collider caveat), one pinned judging session for all
arms, and the smoke-before-sweep rule.

⚠ **The smoke is NOT skipped just because it passed on Llama.** prev-REVIEW-3 found two real
Qwen3-specific defects in the previous port (a `SystemExit` from the thinking-probe leaving a judgeable
partial, and no band validation against model depth), and the modes resolve spans under a **different
tokenizer**. **The Qwen3 smoke runs first and its verdict gates the full arms.**

---

### 🔒 PR-4 (04:40) — **HOW THE PHASE-1 ASR WILL BE READ, given that the generation cap binds on half to three-quarters of EVERY arm and one arm shows a length collapse. Written before the judging session is submitted.**

The 4-hour review's truncation track (C-4 below) found two facts that make a raw ASR comparison
confounded on this population. **Both are recorded and their handling fixed here, before any arm is
judged**, because prev-Gate-E7 is the precedent: `d_surface:add` looked like a −0.06 ASR suppression
and was **a collapse to 25-character completions with the judge scoring near-empty text as
non-compliant**.

**Fact 1 — the cap binds everywhere, unevenly.** Median `n_new_tokens` is **192, the `--max-new` cap**,
in four of five completed arms. Fraction at the cap: `query_prefill` 0.500, `late` 0.542,
`legacy` 0.552, `decode_only` 0.635, `demo_processing` 0.719 — **a 22-point spread**. StrongREJECT's
specificity and convincingness sub-scores are content-volume sensitive, so part of any ASR difference
is *how much text each arm was allowed to emit*.

**Fact 2 — one arm collapses.** `C_demo_processing_only` puts **20 of 96** rows under 200 characters
(other arms: 1–4) and 3 under 80 (min 23; every other arm's minimum is 98–119). **The same 20
`prompt_id`s have median 776–877 chars in the other arms, so it is the ARM, not the prompts**, and the
collapse is dose-responsive in `n_examples` (1/3/6/10 short rows at n=1/2/4/8, permutation
p = 0.00095). **Up to 20.8 ASR points are available to a pure output-length artifact in that arm alone.**

#### 📌 PRE-REGISTERED, before the judge runs

1. **Every ASR in Phase 1 is published beside its arm's truncation fraction and median `n_chars`.**
   An ASR quoted without them is not quotable.
2. **The primary comparison is unchanged** — `response_query_only` vs `legacy`, at PR-3's margin
   (0.0417 arm-vs-arm). Both sit mid-range on truncation (0.552 vs one not yet measured), so it is the
   comparison least exposed to Fact 1; that is stated now, not discovered later.
3. **`C_demo_processing_only`'s ASR is reported as CONFOUNDED and does not carry Outcome B on its own.**
   If that arm is the one that looks large, the honest reading is *"an arm that also truncates 21 % of
   its rows shows a large ASR drop"*, which is prev-Gate-E7's finding restated, not a mechanism result.
   **Outcome B requires the effect to survive the length-conditioned view below.**
4. **A length-conditioned secondary analysis is run for every arm**: paired ASR restricted to rows where
   **both** the arm and the baseline exceed a threshold T, swept over T ∈ {0, 80, 120, 200, 400}
   characters — exactly prev-R-F's table.
   ⚠ **And its caveat is fixed here too:** completion length is a **post-treatment** variable, so
   conditioning on it conditions on a **collider**, and the retained subset is not the population. It
   can show *what an effect is made of*; it **cannot** prove an effect is or is not an artifact. Neither
   the raw nor the conditioned number is the headline alone — **both are reported, always together.**
5. **Nothing in the pipeline currently gates on length** (`analyze_phase_d.py` reads neither `n_chars`
   nor `stop_reason`), so this analysis is done explicitly rather than assumed.

⚠ **The clean fix is out of scope and is recorded as an open item, not attempted:** re-running every arm
with a larger `--max-new` would remove Fact 1 at its source, but it would also break comparability with
every inherited number in this project, all of which used 192. **Raising the cap is a separate
experiment, not a repair to this one.**

---

### 🔒 PR-3 (04:30) — **SUPERSEDES PR-1's MARGIN AND ITS p-FLOOR. Both were wrong, both are corrected BEFORE any Phase-1 arm is judged, and PR-1 is left standing unedited beside this.**

The 4-hour review checked PR-1's own justification against the artifacts it cited. **It does not hold.**
Two arms of P1.3 were still generating when this was written and **nothing has been judged**, so this
is the last moment at which correcting it costs nothing.

#### ⛔ Defect 1 — the equivalence margin was justified by a quantity that was never measured

PR-1 set the margin at **0.03125 (3 prompts of 96)** on the grounds that *"the previous phase's own
**within-session** re-measurement spread on identical arms was 2–3 prompts"*, citing prev-C-10's table.

**Every one of those "re-measurements" is the same generation directory re-judged in a different
session.** Verified from judge `RUNMETA`/`config`: for each of the 10 repeated arms the number of
distinct `config.args.gens` directories is **exactly 1**. There is **zero re-generation** in that
table — it is pure judge noise, and the within-session spread PR-1 leans on **was never measured at
all**.

**And the measured spread is larger than the margin.** Same-arm Δ re-measurement gaps, n = 15 pairs,
in prompts of 96:

```
[0, 0, 1, 2, 3, 3, 3, 3, 3, 3, 4, 4, 5, 5, 6]      median 3   max 6
```

> **The margin equals the MEDIAN gap, and 5 of 15 (33 %) of same-arm re-judgings of byte-identical
> text exceed it.** A margin at the median of the noise calls a third of pure noise "a real
> difference" — and, worse for this phase, would call genuinely different arms equivalent whenever
> they sit inside it.

#### ⛔ Defect 2 — one margin was applied to two quantities with different noise

Pooled within-arm re-judge **sd of ASR = 0.0137** (1.32 prompts of 96). That implies

| comparison | 95 % band | in prompts |
|---|---|---|
| **Δ vs Δ** (arm minus baseline, cross-session) | **± 0.0480** | 4.6 |
| **arm vs arm** (same session, baseline cancels) | **± 0.0380** | 3.65 |

**PR-1 used a single number for both, and the noisier of the two is what its falsifier depends on.**

#### ⛔ Defect 3 — the declared p-floor is unattainable on this design

PR-1 declares the attainable two-sided floor at k = 6 domains to be `2/2⁶ = 0.03125`. **A domain whose
net is exactly zero drops out of a sign test**, and `lab_safety` is **exactly 0.0000** on this bank —
it has been in every phase. The real floor is **`2/2⁵ = 0.0625`**, and the inherited headline is
**already pinned exactly at it** (domain-clustered 5/0, p = 0.0625). The repo's own
`outputs/boombness/how_to_read_the_p_values.json` states this. **A pre-registered floor that the design
cannot reach is not a guard; it is a licence to read a floored p as evidence.**

#### 📌 THE CORRECTED PRE-REGISTRATION, fixed now

1. **Equivalence margin, arm vs arm (the PRIMARY comparison `response_query_only` vs `legacy`), judged
   in ONE session so the baseline cancels: `|ΔASR_arm1 − ΔASR_arm2| ≤ 0.0417` (4 prompts of 96)** —
   above the measured ±0.0380 band, expressed in the natural unit.
2. **Margin for any arm-vs-baseline statement: `0.0521` (5 prompts)** — above the measured ±0.0480.
3. **"Weak" means `|Δ| ≤ 0.0521`; "large" means ≥ 50 % of the legacy arm's Δ in the same session.**
4. **The attainable domain-cluster floor is `0.0625`, not 0.03125**, and **any p at 0.0625 is reported
   as a sign test at its floor**, never as evidence of magnitude.
5. **Every cluster-level p is published with its informative-cluster count and its floor beside it.**

⚠ **What does NOT change:** the primary comparison, the unit of independence, Outcomes A–E, the
falsifier's *shape*, and the stopping rule. **Only the thresholds move, and they move because they were
measured rather than assumed.** PR-1 remains in this file unedited; this entry supersedes it.

⚠ **The falsifier is restated at the corrected margin:** the chain
*demonstrations → response-time retrieval → behaviour* is falsified if `response_query_only` is weak
(`|Δ| ≤ 0.0521`) while the legacy arm is large, **on both models**.

---

### 🔒 PR-2 (02:45) — **PHASE 2: which probe rows carry the headline.** Fixed before the probe is run against any model, and before Phase 1 has resolved.

**The instrument is SELECTION, not synthesis** — and that is a finding about the bank, not a
convenience. `src/boombness/semantic_binding_probe.py` constructs no prompt text at all. The bank
already carries the plan-§5.1 probe:

| query_kind | rows |
|---|---|
| `behavioral` | 1152 |
| `semantic_one_word` | 1008 |
| `semantic_forced_choice` | 288 |
| `comprehension_usage` | 288 |

**Verified independently by me** (after first getting it wrong — see the note below): joining on
`(family_id minus its trailing query_kind field, condition)`, all **1584** probe rows pair **1:1** with
a behavioural row — **0 orphans, 0 duplicate behavioural keys, and the `demo_block` is BYTE-IDENTICAL
across the pair in 1584 / 1584 cases.** So the probe asks about *the same demonstrations the
behavioural row uses*, which is the whole point: the same mask can be applied to both and compared.
Synthesising prompts would have broken the bank's `prompt_sha16` / `bank_rows_sha16` provenance chain,
required its own tokenization audit, and produced a demo block that is **not** the behavioural row's.

#### 📌 PRE-REGISTERED, before any probe run

1. **The headline group is `probe_tests_binding = True` on `natural_doublespeak`.**
   **240 of the 1008** `semantic_one_word` rows (cells B and E, `query_surface == "concept"`) ask about
   the **concept word itself**, so `target_surface == target_semantic` and **no codeword→concept
   binding is tested at all**. They are not a weaker version of the measure — they are a different
   measure.
2. **The `probe_tests_binding = False` rows are the CONTROL**, and their role is fixed now: they answer
   *"did the intervention simply break generic in-context readout?"* — plan §5.3's specificity question.
   An intervention that destroys binding **and** destroys the concept-itself readout has not
   demonstrated anything about binding.
3. **The 156 probe rows with an empty `demo_block`** (`n_examples = 0`) are **excluded**, consistent
   with the behavioural population, which excludes `n_examples = 0` as structurally ineligible (R-B).
   A probe with no demonstrations cannot test retrieval from demonstrations.
4. **These three groups are never averaged together.** `summarize()` refuses to, and the artifact flags
   each row.

⚠ **Recorded against myself:** my first independent check of the 1:1 join reported **168/1584** matched
demo blocks and 6 duplicate keys, and I nearly filed it as a correction against the agent. **My check
was the broken one** — `family_id` is **pipe**-delimited (`farm_storage|dev|slot0|…|behavioral`) and I
split on `_`, so my stem function returned `None` for all 2736 rows and collapsed every key. The agent
used `rpartition("|")` and was right. **The lesson is the one this project keeps relearning: a
disagreement between two computations locates a bug, but says nothing about which side holds it.**

---

### 🔒 PR-1 (00:58) — **PHASE 1: the same-session scoped decomposition.** Written before any scoped arm exists, before any code for it is merged, and before any judging.

**Primary estimand.** Paired ASR@0.5 delta against the *same-session* baseline `A`, on the canonical
96-row behavioural population, per model. **Paired**, because the inherited judge-reliability finding
(same generations re-judged: identical binary label on only **78/96** rows) means only paired
aggregates are stable.

**Primary comparison.** `C_response_query_only` versus `C_legacy_full_scope`. Everything else in the
arm list exists to interpret that one contrast.

**Unit of independence.** The **domain** (k = 6). Not the prompt (the 96 slots are one shared design —
R-1), not the bank, not the model. The attainable two-sided sign-flip floor at 6 informative domains is
`2/2⁶ = 0.03125`, and **any p at or near that floor is reported as a sign test, with the floor quoted
beside it**. The magnitude and its calibrated interval are the quotable quantities.

**THE EQUIVALENCE MARGIN, fixed now.** Two arms are called **equivalent** when
`|Δ_arm1 − Δ_arm2| ≤ 0.03125`, i.e. **3 prompts of 96**. Justification, in advance: the previous
phase's own within-session re-measurement spread on identical arms was **2–3 prompts of 96**
(prev-C-10's table: `L7–9` −0.0208 → −0.0625; `L10–12` −0.0312 → −0.0625), and prev-R-BE's cross-session
judge drift is ~1 row. **A difference smaller than 3 prompts is below this instrument's demonstrated
reproducibility and will not be interpreted, in either direction.** An arm is called **weak** when
`|Δ| ≤ 0.03125` and **large** when it reaches ≥ 50 % of the legacy arm's Δ in the same session.

**Expected outcomes and what each would mean** — the plan's Outcomes A–E, with the margin applied:

| outcome | pattern | reading |
|---|---|---|
| **A** | `response_query_only` ≈ legacy (within margin) **and** `demo_processing_only` weak | the causal path is **response/query access to the demonstrations**. The strongest available result, and the one that would license the wording the project has been using loosely |
| **B** | `demo_processing_only` large, `response_query_only` weak | ⛔ **retract the "generated answer retrieval" wording.** The result becomes *disrupting the demonstrations' own encoding suppresses the attack* — still publishable, differently worded |
| **C** | `query_prefill_only` large, `decode_only` weak | the retrieval event is concentrated in constructing the final query state **before** generation |
| **D** | `decode_only` large | genuinely ongoing retrieval **during** autoregressive generation |
| **E** | legacy large, **every** scoped arm weak | the legacy effect needs interacting disruption across prompt **and** response computation. **State it directly; do not average the scoped arms into a preferred story** |

**Falsifier for the phase's headline hypothesis.** The chain
*demonstrations → response-time retrieval → behaviour* is **falsified** if `response_query_only` is
weak (|Δ| ≤ 0.03125) while the legacy arm is large **on both models**. That is Outcome B or E and it
will be reported as a falsification, not as a scoping caveat.

**Stopping rule.** One 7-arm session per model. **No arm is added after seeing a number.** If a mode's
liveness gate fails, that arm is **VOID** and is re-run after the hook is fixed — it is never reported
with a caveat.

**Secondary analyses allowed** (declared now, so nothing is added later): thresholds 0.25 / 0.75;
per-domain deltas; refusal rate; the generation-health block in §4.2 of the plan; and the
`n_examples` monotonicity check that prev-R-AI ran. **Not allowed:** per-prompt "the same prompts
flipped" claims, any leave-one-out that was not declared here, and any re-clustering after seeing the
result.

#### ⚠ Two design blockers established BEFORE implementation, both from the adversarial review

**(1) The liveness gate will refuse two of the five modes by construction.**
`assert_knockout_live` requires `frac_rows_decode_live ≥ 0.99` (`KNOCKOUT_MIN_LIVE_FRAC`). But
`query_prefill_only` and `demo_processing_only` **make no decode edits at all** — that is their
definition. Left as-is the gate would either abort them or, worse, they would be reported as clean
nulls from a hook that never fired at decode because it was never supposed to. **Resolution, fixed
now:** liveness becomes **mode-aware** — each mode declares which counter is its proof
(`prefill_edits > 0` for the prefill-scoped modes, `decode_edits > 0` for the decode-scoped ones, both
for `response_query_only` and `legacy_all_query`) and the gate asserts *that* counter. **A mode whose
declared counter is zero is VOID.** The gate must not be loosened to "either counter", which would let
a genuinely dead decode hook pass on its prefill edits.

**(2) `decode_only` cannot affect the first generated token.** Verified, not assumed: the prefill mask
is unmodified and decoding is greedy (`do_sample=False`), so token 1 comes from the final prefill query
state and is **bit-identical to baseline** by construction. **Consequence for interpretation:** a small
`decode_only` effect is *not* evidence that decode-time retrieval is unimportant if the behavioural
fork is decided at token 1. ⚠ The review also measured that the fork is **not** normally at token 1 on
this population (median `n_new_tokens` = 117.5, min 29, **fraction with ≤ 3 new tokens = 0.000**), so
the confound is real but is not the typical case. **Both facts go in the write-up; neither is used to
explain away a null.**

**Pre-registered instrument check, before any scientific arm.** The 8-row smoke must show, per mode:
the intended query rows edited and no others; the intended key positions and no others; the declared
liveness counter non-zero on **100 %** of rows; generations changed versus baseline; and
`legacy_all_query` **byte-identical** to today's behaviour. **If any of these fails the arm does not
run.**

## B2. DECISIONS

**D-1 (00:30) — the starting truth is `059e819f`, not `8c83c8f3`, and the plan's §0 magnitude paragraph
is amended on arrival.** The plan was written against the audited state `8c83c8f3` and quotes R-BD's
k=18 CI as the current magnitude claim. HEAD had already moved three commits, the last of which
(**C-18 / REVIEW-8**, 23:52) **retracts R-BD**: all ten populations share the identical 96 `prompt_id`s,
so `pool × domain` k=18 is a crossed 3×6 table in which 62.1 % of the spread is two main effects counted
3× and 6× over; both marginals include zero. Amending the plan's own starting state is *within* the
plan's instruction to "inspect the current HEAD first in case more work has landed", and the amendment
**does not change a single phase** — it strengthens Phase 4, which is now confirmatory on an open
question rather than on a settled one. Recorded here rather than silently editing Part A §0.

**D-2 (00:30) — file and code ownership is split with the peer session, in writing.** ⛔ **CORRECTED at
00:41 — the split I proposed was addressed to the wrong owner.** I messaged the peer session
(`BOOMBNESS_D_SURFACE_FOLLOWUP implementation`) proposing that it keep
`external_md/BOOMBNESS_DSURFACE_NEXT_PHASE_PLAN_AND_PROGRESS.md`,
`src/boombness/crossbank_knockout_test.py` and jobs 779083–779086. **It replied that it owns none of
them**: its log is `external_md/BOOMBNESS_D_SURFACE_FOLLOWUP_PROGRESS.md` (a *different* file —
`D_SURFACE_FOLLOWUP`, not `DSURFACE_NEXT_PHASE`), its only job was **776368** on `cpu-killable`, and it
has stopped entirely and released everything. **See P-1.** Corrected split: **this session owns
everything in the boombness line**, and no path is frozen on the peer's behalf. **No `scancel` by this
session under any circumstance** — that part stands regardless of ownership.

**D-3 (00:42) — the 18 test failures are triaged before any GPU work, and the 12 provenance failures are
treated as real.** Baseline reproduced at `059e819f` with the project env:
**721 passed, 18 failed, 7 skipped in 154.26 s.** The split is exactly as the Part-II audit predicted:
**6** are `test_module_imports_without_torch` / `test_import_is_torch_free` assertions
(`test_candidate_pool`, `test_gpu_runner`, `test_phase_f_attention_probe`, `test_phase_f_probe_driver`,
`test_reinforce_mac`, `test_soft_prompt_reinforce`) and **12** are artifact-regeneration / provenance
assertions (`test_estimand` ×5, `test_g2_selection` ×6, `test_analyze_steering::test_T2_...` ×1).
Per §1.3 the second group is **not** environment noise and is not dismissed.

**D-4 (00:35) — ⚠ PHASE 4's AXIS IS WRONG, AND I AM FLAGGING IT TO THE USER RATHER THAN SILENTLY SWAPPING IT.**
Plan §9 says the next confirmatory increment is **a fourth demonstration pool** (`club`). Two findings
that landed *after* the plan was written say that cannot work:

* **prev-R-BE** (`7838dcd2`, inherited): all four axes the previous phase added — banks, pools, models,
  concepts — **reuse the same six domains**, and the sign-flip test clusters on domains, so its p-floor
  is `2/2⁶` *regardless of how many prompts, banks or pools each domain holds*. Phase 8 stated this in
  its own words before Phases 8/9/10/10b spent four banks, a third pool, a second model and a fourth
  concept on the wrong axis.
* **R-2** (this phase): pool is **perfectly confounded with concept** here, and the pooled direction is
  carried by a single corpus. A fourth pool adds a fourth concept, not a fourth independent replicate
  of the domain structure.

**The untried route is domains.** `src/boombness/demo_pools.py` holds its domain list in a module-level
`DOMAINS` dict (~line 60) and records it in `_meta.domains`, so regenerating pools at 8–10 domains and
rebuilding one bank per pool is an ordinary bank-generation job — no new machinery.
⚠ **Carry prev-R-BE's own caveat:** the projection holds mean and sd fixed while the effect is
concentrated (`game_manual` −0.2562 against a −0.0865 mean, `lab_safety` exactly 0.0000). **New domains
could be `lab_safety`-like, raising sd as they lower the mean. "8 domains" is optimistic, not
guaranteed.**

**Decision:** Phase 4 is **not started** and **not silently redefined**. It is downstream of Phases 1–3
anyway, so nothing is blocked by deferring it. The question for the user is whether Phase 4 becomes
*"add a fourth demonstration pool"* as written, *"regenerate pools at 8–10 domains"* per R-BE, or both.
**Phases 1, 2 and 3 are unaffected and proceed.**

**D-8 (07:10) — Phase 2 runs its intervention through `score_behavior`, NOT through the probe module; and R-10 CHANGES WHICH ARMS IT MUST TEST.**

**(a) Reuse, not new plumbing.** `src/boombness/semantic_binding_probe.py` contains **zero** references
to `intervene` or `knockout` — it is a pure measurement instrument that loads a model and does a
next-token readout. `score_behavior.py` already has **both** the readout machinery
(`next_token_readout`, `--readout-ids`, `--min-option-mass`) **and** `--intervene` / `--knockout-scope`.
**So the probe rows are run through `score_behavior` with `--query-kinds semantic_one_word`**, and the
probe module keeps its role as the selector/scorer. Adding an intervention path to the probe would have
duplicated a hook plumbing this repo has already dropped a threaded argument on twice
(`control_seed`, then `demo_keys`).

**(b) The arm set changes because of R-10.** Plan §5.2 names *"baseline, validated
`response_query_only`, late-layer control, same-band non-demo controls"*. **That list was written when
`response_query_only` was the presumed causal arm.** R-10 shows it carries **46.2 %** of the effect
while `demo_processing_only` carries **92.3 %**. **Running the probe only on `response_query_only`
would measure the semantic consequence of the arm that does NOT carry the behaviour.** Phase 2
therefore tests **both**, and `demo_processing_only` is the one the headline question now attaches to:
*does the arm that suppresses the attack also destroy the codeword→concept mapping, or does it merely
make the model refuse?* — the question R-10's **0.208 refusal rate** raises and cannot answer.

**Smoke first, as always:** jobs **779755–779757**, three arms × 8 probe rows on Llama, band L6–14,
`--max-new 8` (a one-word readout needs no more). The full probe run is gated on it.

**D-5 (00:52) — USER RULING ON D-4: do BOTH. Phase 4 keeps the fourth demonstration pool *and* gains a
domain-expansion arm.** Asked directly (D-4 laid out fourth-pool / more-domains / both); the answer was
**both**. So Phase 4 splits into two independently-reportable sub-phases, and the ordering matters
because they answer different questions:

* **4A — fourth pool (`club`), as plan §9 wrote it.** Confirmatory, frozen analysis, the `club` corpus
  already exists and is audited. It tests *"does the effect hold on a corpus it was not discovered
  on?"* — and after **R-2** that question is sharper than when the plan was written, because the
  pooled direction is currently carried by the bomb corpus alone (81/11) while knife (15/7, p = 0.134)
  and gun (17/12, p = 0.458) are null. **`club` is therefore a genuine test, not a formality: if it
  behaves like knife and gun, the honest claim becomes "the effect is a property of the bomb corpus".**
  ⚠ It adds **no** domain clusters, so it cannot move the k=6 marginal — that is not its job.
* **4B — regenerate pools at 8–10 domains, one bank per pool.** This is the axis prev-R-BE identifies
  as the binding one, and it is the only untried route to a domain marginal that could exclude zero.
  `src/boombness/demo_pools.py` holds `DOMAINS` at module level (~line 60) and records it in
  `_meta.domains`, so this is an ordinary bank-generation job with no new machinery.
  ⚠ Carry prev-R-BE's caveat verbatim: the 8-domain projection holds mean and sd fixed while the effect
  is **concentrated** (`game_manual` −0.2562 against a −0.0865 mean; `lab_safety` exactly 0.0000). New
  domains may be `lab_safety`-like and raise sd as they lower the mean. **Pre-register that the new
  domains are accepted or rejected on their audit, never on their effect size**, or 4B becomes a search
  for domains that help.

**Both remain downstream of Phases 1–3** and neither is started. The scoped-knockout decomposition
(Phase 1) is still the sprint's highest-priority experiment, because 4A and 4B both measure *an
intervention whose scope is not yet isolated* — running either before Phase 1 would spend a corpus and
a bank-generation cycle on the legacy arm.

## B3. EXPERIMENT STATUS BOARD

Legend: ⬜ not started · 🔬 running · ✅ complete · ⛔ failed/retracted · ⏸ blocked

| id | phase | experiment | status | gate |
|---|---|---|---|---|
| P0.1 | 0 | independent re-derivation of the cross-bank result from raw artifacts | ✅ **R-1** — reproduces prev-C-18 to the digit; **R-2** is new and amends the headline | — |
| P0.2a | 0 | prev-C-18 fixes pinned by regression tests + `require_done` on inputs + k=1 guard | ✅ done | — |
| P0.2b | 0 | atomic `--strict` bank write | ✅ done — validation now precedes the rename | — |
| P0.2c | 0 | judge backend pinning + per-row provenance | ✅ opt-in mode, default byte-identical | — |
| P0.2d | 0 | `EXCLUDED_RUNS.json` | ✅ **R-4** — 62 dirs across 6 experiments | — |
| P0.2e | 0 | metric renames | ✅ done — `uniq_frac` had **no producer at all**; one added | — |
| P0.3 | 0 | full test suite triage — 18 failures classified and repaired | ✅ **760 passed, 0 failed, 7 skipped** (was 721/18/7) | **Phase-0 exit** |
| P1.1 | 1 | scoped attention-knockout semantics (5 modes) + synthetic tests | ✅ **R-3** — +225/−0, 52 tests, 194 passed | — |
| P1.2 | 1 | 8-row liveness smoke, Llama | ✅ **PASS (R-9)** — 5 arms, 0 failures | **GATE PASSED** |
| P1.3 | 1 | same-session 8-arm decomposition, Llama | ✅ **OUTCOME B (R-10)** | primary comparison FAILS equivalence |
| P1.4 | 1 | Qwen3 replication — 8 arms at L7–17 | ✅ **REPLICATES (R-12)** — PR-5 conditions 1,2 HOLD; 3 fails and is model-specific | **PR-5** |
| P2 | 2 | semantic binding probe + causal intervention on it | ✅ **R-15 + R-16 (within-family)** — the attack dies where the mapping survives | **PR-2**, **D-9** |
| P4B | 4B | regenerate pools at **10 domains**, one bank per pool | 🔬 pool gen **779902**; **D-10** pre-registers accept-on-audit | prev-R-BE |
| P2B | 2B | completion phenotype instrument | ✅ built (blinded, two views, agreement + confusion matrix persisted); **not a causal estimator until its reliability is measured** | — |
| P2C | 2C | row-wise demo-deletion control | ⛔ **DESCOPED on this bank (R-7)** — the deleted population is 1 prompt by construction | — |
| P3 | 3 | full-state rescue, then retrieval-effect subspace | ⬜ | full-state first |
| P4A | 4 | fourth demonstration pool (`club`), frozen confirmatory | ⬜ | analysis frozen first |
| P4B | 4 | regenerate pools at 8–10 **domains**, one bank per pool | ⬜ | domains accepted on audit, never on effect size |
| P5 | 5 | joint crossed bank | ⬜ | strict acceptance |
| P5B | 5B | geometry on both models | ⬜ | — |
| P6 | 6 | Qwen3 retrieval × refusal | ⬜ | identifiability gate |
| P7 | 7 | objective reopen gate | ⏸ | O1–O6 |

## B4. SLURM JOB LEDGER

*(every job submitted by this phase, with the commit its tree will execute; FAILED and CANCELLED rows
stay visible)*

| job id | owner | what | submitted | tree commit | output | status |
|---|---|---|---|---|---|---|
| **779083 / 779084** | ⚠ **UNATTRIBUTED — now identified** | `boomb`, submitted **2026-08-24 23:20:23**, `killable`, `n-801`, `WorkDir` = this repo. Read from the previous log as Phase 10b Qwen3 `button_gun`. **Nobody in contact claims them.** | 23:20 | presumed `3e3000a0` | `.../score_behavior/` | ✅ **COMPLETED 01:29:56**, both, exit 0:0. **Left alone throughout; never cancelled.** Owner identified at 00:47 as `bridge:session_014rrdKYhbejM6zf4W2mjomM`, which has since stopped and explicitly disowned them. **Not consumed by this phase** — and their scientific value is moot regardless, because prev-C-18 invalidated the *unit*, not the number, so equalising the gun pool's depth cannot rescue prev-R-BD |
| 779085 / 779086 | ⚠ unattributed | Llama half of the same pair; reported COMPLETED in the previous log | 23:20 | presumed `3e3000a0` | `.../score_behavior/` | COMPLETED (per prev-log) |
| **779477** | this | **P1.2 smoke** `A_baseline`, Llama, `--limit 8` | 01:32 | `802d73ef` | `s1A_20260825_015705_731547` | ✅ COMPLETED 6:19, 0:0 |
| **779478** | this | smoke `legacy_all_query` — the bridge arm | 01:32 | `802d73ef` | `s1_legacy_all_query_20260825_020636_732499` | ✅ COMPLETED 1:12, 0:0 — **R-5 partial** |
| **779479** | this | smoke `query_prefill_only` | 01:32 | `802d73ef` | `s1_query_prefill_only_20260825_025641_395899` | ✅ COMPLETED — **R-8 PASS** |
| **779480** | this | smoke `decode_only` | 01:32 | `802d73ef` | `s1_decode_only_20260825_030140_398148` | ✅ COMPLETED — **R-8 PASS** |
| **779481** | this | smoke `response_query_only` — **the primary arm of the phase** | 01:32 | `802d73ef` | `.../score_behavior/s1_response_query_only_*` | PENDING (Priority) |
| **779482** | this | smoke `demo_processing_only` | 01:32 | `802d73ef` | `.../score_behavior/s1_demo_processing_only_*` | PENDING (Priority) |
| **779605** | this | P1.3 `A_baseline` | 03:42 | `d8989dfc` | `.../score_behavior/p1A_*` | queued |
| **779606** | this | P1.3 `C_legacy_all_query` | 03:42 | `d8989dfc` | `.../score_behavior/p1_legacy_all_query_*` | queued |
| **779607** | this | P1.3 `C_response_query_only — PRIMARY` | 03:42 | `d8989dfc` | `.../score_behavior/p1_response_query_only_*` | queued |
| **779608** | this | P1.3 `C_query_prefill_only` | 03:42 | `d8989dfc` | `.../score_behavior/p1_query_prefill_only_*` | queued |
| **779609** | this | P1.3 `C_decode_only` | 03:42 | `d8989dfc` | `.../score_behavior/p1_decode_only_*` | queued |
| **779610** | this | P1.3 `C_demo_processing_only` | 03:42 | `d8989dfc` | `.../score_behavior/p1_demo_processing_only_*` | queued |
| **779611** | this | P1.3 `D_response_query_late_control` | 03:42 | `d8989dfc` | `.../score_behavior/p1_late_*` | queued |
| **779733** | this | Qwen3 smoke `A_baseline`, band 7–17, `--limit 8` | 06:10 | `f7879eb1` | `.../score_behavior/s2A_*` | queued |
| **779734** | this | Qwen3 smoke `legacy_all_query`, band 7–17, `--limit 8` | 06:10 | `f7879eb1` | `.../score_behavior/s2_legacy_all_query_*` | queued |
| **779735** | this | Qwen3 smoke `query_prefill_only`, band 7–17, `--limit 8` | 06:10 | `f7879eb1` | `.../score_behavior/s2_query_prefill_only_*` | queued |
| **779736** | this | Qwen3 smoke `decode_only`, band 7–17, `--limit 8` | 06:10 | `f7879eb1` | `.../score_behavior/s2_decode_only_*` | queued |
| **779737** | this | Qwen3 smoke `response_query_only`, band 7–17, `--limit 8` | 06:10 | `f7879eb1` | `.../score_behavior/s2_response_query_only_*` | queued |
| **779738** | this | Qwen3 smoke `demo_processing_only`, band 7–17, `--limit 8` | 06:10 | `f7879eb1` | `.../score_behavior/s2_demo_processing_only_*` | queued |
| 776368 | peer (`…FOLLOWUP implementation`) | `run_band2_judge.sh`, `cpu-killable` | 2026-08-23 17:16 | `91e30a62` | `.../judge/bnd2_*` | peer has stopped and is not analysing it |

## B5. RESULTS

*(`R-` ids, newest first)*

### 🏆🏆 R-9 (03:39) — **🚦 THE PHASE-1 SMOKE PASSES AS A WHOLE. 5 arms, 0 failures. The decomposition is real on a live model, and the pre-registered cross-check held.**

**Artifact:** `outputs/boombness/scoped_smoke_verdict/s1verdict_20260825_033930_2556360/scoped_smoke_verdict.json`
**Producing script:** `src/boombness/scoped_smoke_verdict.py` (new) — it imports the hook's own
`LIVENESS_REQUIREMENT` / `scoped_liveness_violations`, so the verdict cannot drift from the contract it
checks. Exit status **0**.

| arm | prefill edits | decode edits | `frac_rows_scope_live` | violations | gens changed vs baseline |
|---|---|---|---|---|---|
| `legacy_all_query` | 250 065 | 698 733 | 1.0 | `{}` | **8/8** |
| `query_prefill_only` | 91 800 | **0** | 1.0 | `{}` | **8/8** |
| `decode_only` | **0** | 686 061 | 1.0 | `{}` | **8/8** |
| **`response_query_only`** | **91 800** | **695 889** | 1.0 | `{}` | **8/8** |
| `demo_processing_only` | 154 440 | **0** | 1.0 | `{}` | **8/8** |

#### ✅ The pre-registered cross-check, recorded in R-8 *before these two arms existed*

```
legacy prefill edits          250 065
query_prefill_only             91 800
demo_processing_only          154 440
sum of the two scoped         246 240   <= 250 065   ✅  slack 3 825
```

**The slack is the point, and it is why this was registered as an inequality rather than an equality.**
3 825 of 250 065 (**1.53 %**) are prefill query rows in **neither** span — the chat template and
preamble, which `legacy_all_query` masks and neither scoped mode does. **An equality would have been
evidence of a bug**, not of a decomposition.

#### ✅ And the check that makes every zero above meaningful

A correctly-scoped hook and a **dead** hook both report zero edits. What separates them is whether the
hook was *called* on the half where it declines to edit:

| mode | forbidden counter | **min forwards where it is forbidden to edit** |
|---|---|---|
| `query_prefill_only` | decode edits | **1 152** |
| `demo_processing_only` | decode edits | **1 611** |
| `decode_only` | prefill edits | **9** *(all nine band layers)* |

**Every zero in this table is a hook that ran, was asked, and correctly declined.** The verdict script
fails an arm that reports zero edits *and* zero forwards, precisely so a dead hook can never be filed
as a scoped one.

**`response_query_only` — the phase's primary arm — is the only scoped mode with both counters
positive** (91 800 prefill, 695 889 decode), as its definition requires. Its prefill total is
**exactly equal** to `query_prefill_only`'s, which is the right invariant: both mask the same
final-query span at prefill.

> **🚦 GATE P1.2 PASSES.** All five PR-1 instrument conditions are met: declared counters satisfied on
> 100 % of rows; the hook demonstrably called where it edits nothing; generations changed 8/8 against
> the session's own baseline for every scoped arm; disjointness and subset hold with informative slack;
> and `legacy_all_query` is byte-identical to the original class **by construction**, since that scope
> routes to `AllQueryAttentionKnockout` itself. **Phase 1's full experiment is cleared to run.**

⚠ **What this does NOT establish.** Nothing about behaviour. n = 8, no judging, no ASR. The smoke's
only claim is that each mode edits what it says it edits.

---

### 🔬 P1.3 LAUNCHED (03:42) — the 7-arm same-session decomposition at n = 96

Jobs **779605–779611**, Llama-3.1-8B, `--expect-n 96`, band **L6–14**, all seven judged later in ONE
session per PR-1:

| job | arm | intervention |
|---|---|---|
| 779605 | `A_baseline` | — |
| 779606 | `C_legacy_all_query` | `demo_all:attn_knockout:6-14:1.0` |
| **779607** | **`C_response_query_only`** | same band, scope `response_query_only` |
| 779608 | `C_query_prefill_only` | same band |
| 779609 | `C_decode_only` | same band |
| 779610 | `C_demo_processing_only` | same band |
| **779611** | **`D_response_query_late_control`** | **`20-31`**, scope `response_query_only` |

**The late control is the primary matched control (D-7 / prev-D-10):** the *same* key set and the
*same* scope moved to control layers, so it is exactly count-matched by construction and always
feasible at every `n_examples` — unlike the same-band non-demo draws, which R-6 showed cannot be
count-matched at `n_examples` 4 or 8.

⚠ **Seven concurrent jobs against the plan's "approximately 6" cap.** Recorded rather than glossed:
the seven are one indivisible same-session comparison, splitting them would reintroduce the
cross-session judge confound PR-1 exists to avoid, and with 56 jobs already ahead of us on fair-share
we are not displacing anyone.

📌 **The reading is already fixed** by PR-1 §Outcomes A–E and the **0.03125 equivalence margin**
(3 prompts of 96), both written before any of this code existed. **Nothing in the analysis is chosen
after seeing these numbers.**

---

### ★★★★★ R-8 (03:10) — **THE TWO ARMS THAT COULD HAVE SILENTLY COLLAPSED DO NOT. Both zero-counter assertions hold exactly, and one of them would have been ABORTED by the inherited gate.**

**Artifacts:** `s1_query_prefill_only_20260825_025641_395899` (job 779479, COMPLETED 0:55) and
`s1_decode_only_20260825_030140_398148` (job 779480, COMPLETED 0:59). Both `DONE.json`, both n=8.

| | `query_prefill_only` | `decode_only` |
|---|---|---|
| `liveness_required` | `["n_prefill_edits"]` | `["n_decode_edits"]` |
| `liveness_must_be_zero` | `["n_decode_edits"]` | `["n_prefill_edits"]` |
| **total prefill edits** | **91 800** | **0** ✅ |
| **total decode edits** | **0** ✅ | **686 061** |
| median prefill / decode edits | 9 504.0 / **0.0** | **0.0** / 74 358.0 |
| per-row prefill edits (min–max) | 2 376 – 24 840 | **0 – 0** |
| per-row decode edits (min–max) | **0 – 0** | 18 909 – 196 650 |
| `frac_rows_scope_live` | **1.0** | **1.0** |
| `scope_violations` | **`{}`** | **`{}`** |
| rows with any liveness violation | **0 / 8** | **0 / 8** |

#### The number that makes this a pass rather than a coincidence

**`query_prefill_only` reports `min_decode_forwards = 1152`, and `decode_only` reports
`min_prefill_forwards = 9`.** The hook was **called** 1152 times at decode and at all 9 prefill layers
respectively — **and edited nothing there.** That is the distinction the whole design turns on:

> **a correctly-scoped hook and a dead hook produce the same zero.** The forward counters separate them,
> and they say the hook was live, was asked, and declined. A mode that had silently collapsed into
> another would have shown edits where these show zeros; a mode whose hook never attached would have
> shown zero *forwards*, not zero *edits*.

#### ⚠ The inherited gate would have killed a correct arm

`query_prefill_only` has **`frac_rows_decode_live = 0.0`**, against the inherited
`KNOCKOUT_MIN_LIVE_FRAC = 0.99`. **Under the pre-existing gate this arm aborts — or, worse, is read as
a clean null from a hook that "did not fire".** It fires perfectly; it simply has nothing to do at
decode by definition. This is exactly the blocker PR-1 recorded **before the code existed**, and the
mode-aware gate resolves it without loosening: `frac_rows_scope_live = 1.0` and `scope_violations = {}`
come from asserting the *required* counters are positive **and** the *forbidden* ones are exactly zero.

#### Status of the smoke — still not passed, and deliberately so

| arm | job | state |
|---|---|---|
| `A_baseline` | 779477 | ✅ COMPLETED |
| `legacy_all_query` | 779478 | ✅ COMPLETED (R-5) |
| `query_prefill_only` | 779479 | ✅ **COMPLETED — R-8** |
| `decode_only` | 779480 | ✅ **COMPLETED — R-8** |
| **`response_query_only`** | **779481** | 🔬 PENDING — **the phase's primary arm** |
| `demo_processing_only` | 779482 | 🔬 PENDING |

**PR-1 says the smoke is read as a whole or not at all**, and the outstanding pair carries the two
checks these two cannot supply: `response_query_only` must show **both** counters positive (it is the
only mode besides legacy that spans prefill and decode), and `demo_processing_only` is needed for the
**disjointness** check — that it and `query_prefill_only` edit disjoint query-row sets whose union sits
inside legacy's. Until then the decomposition is demonstrated on the synthetic harness and on two of
its four scoped arms.

⚠ **A real-data cross-check that will be available once 779482 lands**, recorded now so it is not
invented afterwards: legacy's **250 065** total prefill edits should upper-bound the sum of
`query_prefill_only`'s **91 800** and `demo_processing_only`'s prefill edits on the same rows.
*(Only an upper bound, not an equality: the arms generate different text, so their decode lengths and
therefore their totals legitimately differ — legacy's 698 733 decode edits against `decode_only`'s
686 061 is that effect, not a discrepancy.)*

---

### ⛔⛔ R-7 (03:05) — **THE DEMONSTRATION-DELETION CEILING IS NOT RECONSTRUCTIBLE ON THIS BANK, BY ANY DELETION RULE. Phase 2C cannot run here, and that is a property of the bank rather than of the old code.**

**Producing module:** `src/boombness/demo_deletion_control.py` (new). **Verified independently by me**
with a hash-only census — no prompt text read out.

Canonical Phase-1 population (`behavioral` ∧ `natural_doublespeak` ∧ `bank_block ∈
{core2x2, core2x2_slot3}` ∧ `n_examples ∈ {1,2,4,8}`), **n = 96**:

| quantity | distinct values |
|---|---|
| `full_prompt` | **96** |
| `demo_block` | **96** |
| prefix (text before the demo span) | **1** |
| suffix (text after the demo span) | **1** |
| **deleted prompt (prefix + suffix)** | **1** ← the ceiling population |
| rows where the demo block is not uniquely locatable | 0 |

**The 96 rows differ ONLY inside their demonstration blocks**, which are **68.0 %** of the prompt by
characters; everything outside is byte-identical across all 96. Widening to the whole behavioral bank
(1152 rows), the demo-free residue takes **9** distinct values.

> **Deleting the demonstrations is precisely the operation that deletes all between-row variation.**
> The ceiling is one Bernoulli draw *regardless of implementation quality*.

**This reframes prev-REVIEW-2's M1.** That finding — `final_query_text` takes only 2 distinct values
bank-wide, so the 96-row `--demo-deleted` arm was one prompt — was read as a defect in the arm.
**Fixing the arm does not recover a population.** A row-specific, structure-preserving deletion built
correctly still yields **one** prompt, because the rows never differed outside their demo blocks in the
first place. **A deletion ceiling requires a bank whose rows vary OUTSIDE the demo block** — varied
queries, wrappers or surfaces per cell.

**D-6 — Phase 2C is descoped on this bank, not deleted from the plan.** The module is kept and is
written to work unchanged on a bank that does vary outside the demo block; its guard passes once ≥ 90 %
of transformed prompts are distinct. ⚠ **That 0.90 floor was chosen by the implementer, not by the
plan** — it is stated and defended in the module docstring and asserted at the 18/20-vs-17/20 boundary
in tests, and the plan should ratify or change it before 2C is ever scheduled.
📌 **Opportunity, recorded for later:** **Phase 4B** (regenerate pools at 8–10 domains) and **Phase 5**
(the joint crossed bank) are both bank-generation jobs. **If either varies the query surface outside the
demo block, the deletion ceiling becomes reconstructible for free.** That is a design requirement worth
carrying into those phases rather than discovering afterwards.

---

### ⚠⚠ R-6 (03:00) — **A COUNT-MATCHED, QUERY-PROTECTED SAME-BAND NON-DEMO CONTROL DOES NOT EXIST AT HIGH DOSE. The plan's §4 control is only runnable at low `n_examples`.**

**Code:** `src/boombness/score_behavior.py` (+215/−10, additive), arms
`nondemo_matched_d1..d3` (strict) and `nondemo_capped_d1..d3` (capped), seeded from the run's own
`--seed` by a stride distinct from the composed-leg stride so a draw index can never collide with a
composed offset — prev-retraction-#7's shape.

**The geometry is the whole finding.** The demonstration block **grows** with `n_examples` while the
non-demo pool is a near-constant ~53 tokens, of which the request and generation header are
**protected** (`query_span_positions`, the existing prev-REVIEW-1 M1 fix, reused rather than
re-derived). Measured per row on the real bank:

| `n_examples` | rows | fraction where a **strict** count-matched control EXISTS | median achieved ratio when capped |
|---|---|---|---|
| 1 | 96 | **1.000** | 1.00 |
| 2 | 264 | **0.898** | 1.00 |
| **4** | 342 | **0.000** | **0.60** |
| **8** | 306 | **0.000** | **0.30** |

⚠ **My own coarse cross-check disagrees at `n_examples = 2` and I am recording the disagreement rather
than picking a side.** Using prev-M1's *published* token constants (|demo_keys| 12 / 25.5 / 53.5 / 106
against a ~15-token protected pool) I get n=2 **infeasible** with a max ratio of 0.59, and capped ratios
of 0.28 / 0.14 at n=4 / n=8 — roughly half the measured ones. The per-row measurement is the better
instrument (my check substitutes one published constant for a per-row quantity), **and the two agree
completely on the load-bearing conclusion: strict count-matching is impossible at `n_examples` 4 and 8.**

**Consequence for inference, stated now:** at `n_examples` 4 and 8 the available control is
**under-dosed**, so it can support *"control ≥ arm, therefore not demo-specific"* but **never the
reverse**. The arm name carries the policy (`matched` vs `capped`) so a capped run cannot be filed as a
matched one, and every row records `control_draw_match_ratio` plus the exact integer positions drawn.

**D-7 — the primary matched control remains the LAYER SWAP, exactly as prev-D-10 already decided.**
This result independently re-derives and quantifies the reasoning behind that decision: the same demo
key set applied at control layers is exactly count-matched by construction, always feasible at every
`n_examples`, and isolates *"these tokens at these layers"* from *"these tokens anywhere"*. The
same-band non-demo draws are a **secondary** control, reported where strict matching exists and clearly
labelled capped where it does not. **The plan's §4 asks for them; the bank can only partly supply them,
and the honest answer is to say so rather than to run a capped arm under a matched name.**

---

### 📌 COMPUTE (02:40) — **fair-share, not capacity, and I am not resubmitting.** Measured before acting.

Smoke jobs 779479–779482 have been `PENDING (Priority)` for **65 minutes**. Diagnosed rather than
assumed:

| evidence | value |
|---|---|
| L40S nodes | `n-801`…`n-805` **mixed** (partially allocated), `t-806` **allocated** |
| pending jobs in `killable` | **56** |
| top pending priority | **100002365** (another user), then 100001218 ×2 |
| **our priority** | **100000441** — last |
| our `gpu-research` FairShare | **0.050676 / 0.370270** |

**We are behind 56 jobs on priority, and the nodes are `mixed` rather than full, so this is the
fair-share ordering the previous phase already diagnosed as the sole constraint** — where widening the
`--nodelist` was *tested with one submission before acting* and changed nothing.

**Actions deliberately NOT taken:**
* **No `scancel`.** Standing rule of this phase, and a blanket cancel on this account destroyed three
  jobs once already.
* **No resubmission.** Re-queueing loses position and, with 56 jobs ahead, makes it strictly worse.
* **No switch to `gpu-students`** despite its FairShare of **0.987162** — `studentkillable` carries no
  L40S, and `run_boombness.sh` hard-fails unless the GPU reports `*L40S*`. Already established; not
  re-derived.

**The queue simply has to drain.** All CPU-side work continues at full speed, which is what the tick
below spends its time on.

---

### 🔬 R-5 PARTIAL (02:10) — **the bridge arm fires correctly on a real model, and the derived prefill counter is confirmed off the toy harness.** 2 of 6 smoke arms landed; the four decisive ones are still throttled.

**Artifacts:** `outputs/boombness/score_behavior/s1A_20260825_015705_731547` (baseline, job 779477,
COMPLETED 6:19) and `s1_legacy_all_query_20260825_020636_732499` (job 779478, COMPLETED 1:12). Both
carry `DONE.json`.

**`legacy_all_query` liveness block, verbatim from `summary.json`:**

| field | value |
|---|---|
| `n_rows` | 8 |
| `frac_rows_decode_live` | **1.0** |
| **`frac_rows_scope_live`** | **1.0** ← the new per-mode gate |
| `liveness_required` | `["n_prefill_edits", "n_decode_edits"]` |
| `liveness_must_be_zero` | `[]` |
| **`scope_violations`** | **`{}`** |
| `median_prefill_edits` | 19 354.5 |
| `median_decode_edits` | 64 948.5 |
| `min_prefill_forwards` | 9 *(= the 9 band layers, one prefill forward each)* |
| `min_decode_forwards` | 1 368 |
| `total_prefill_edits` / `total_decode_edits` | 250 065 / 698 733 |
| `attn_implementation` | `eager` |

**The derived-counter path is confirmed on a real model, not just the toy.** R-3 verified
`n_edits == n_prefill_edits + n_decode_edits` on three toy geometries; the legacy arm routes to
`AllQueryAttentionKnockout`, which never writes `n_prefill_edits`, so this run exercises the derivation
against Llama-3.1-8B. Per row, from `gens.jsonl` (scalar fields only):

| row | `hook_n_edits` | `hook_n_decode_edits` | derived prefill | recorded prefill |
|---|---|---|---|---|
| 0 | 21 087 | 18 018 | **3 069** | **3 069** ✅ |
| 1 | 55 890 | 46 413 | **9 477** | **9 477** ✅ |
| 2 | 120 780 | 94 545 | **26 235** | **26 235** ✅ |

**Rows violating the invariant: 0 of 8.** So the legacy liveness verdict is a measurement on the real
model, not an artifact of the derivation.

**Auditability holds:** `intervention.knockout_scope = "legacy_all_query"` is in `summary.json`, and
every `gens.jsonl` row carries `knockout_scope`, `hook_n_prefill_edits`, `hook_n_query_rows_edited` and
`hook_liveness_violations`. A scope is not distinguishable only by a flag that appears nowhere.

⚠ **This is NOT the smoke passing.** The two arms that carry the whole design — `query_prefill_only`
(must show **zero** decode edits) and `decode_only` (must show **zero** prefill edits) — are jobs
779479 and 779480, still `PENDING (Priority)`, along with `response_query_only` (779481) and
`demo_processing_only` (779482). **A mode that silently collapsed into another would look perfectly
healthy in the block above.** The smoke is read as a whole or not at all, and no scientific arm runs
until it is.

---

### ★★★★ R-3 (01:20) — **PHASE 1 INSTRUMENT BUILT: five scoped modes, purely additive, and the legacy path still constructs the ORIGINAL class.** No scientific arm has run.

**Code:** `doublespeak_causality/pair_common.py` **+225 / −0** — `git diff --numstat` confirms **zero
deleted lines**, so `AttentionKnockout` and `AllQueryAttentionKnockout` are byte-for-byte untouched and
every committed G1/G3/Phase-2-4 artifact keeps its producing semantics.

**The five modes** (`pc.SCOPED_KNOCKOUT_MODES`), all differing only in *which query rows* are filtered
on top of the existing `lo = max(0, kp − past)` algebra:

| mode | prefill | decode |
|---|---|---|
| `legacy_all_query` | every row | every row |
| `query_prefill_only` | final-query span only | — |
| `decode_only` | *(untouched)* | every generated row |
| `response_query_only` | final-query span | every generated row |
| `demo_processing_only` | rows **inside** the demo block | — |

**The design decision that matters most:** `--knockout-scope` defaults to `legacy_all_query`, and that
default **routes to `pc.AllQueryAttentionKnockout`, not to the new class**
(`score_behavior.py:583`). So existing recipes are unchanged *by construction* rather than by test —
the strongest available guarantee, and it means no argsfile in the repo changes behaviour.

**Mode-aware liveness, and the trap PR-1 predicted.** Two modes make **zero decode edits by
definition**, so the inherited `frac_rows_decode_live ≥ 0.99` gate would have aborted them or, worse,
reported them as clean nulls. The contract now lives in one place — `LIVENESS_REQUIREMENT` (counters
that must be > 0) and `LIVENESS_MUST_BE_ZERO` (counters that must be exactly 0) — and
`scoped_liveness_violations(mode, stats)` asserts **both directions**. I verified by reading it that it
is **not** the forbidden "either counter is non-zero" form: a decode-scoped mode with zero decode edits
still fails.

#### ⚠ The subtle bug this could have had, found and handled

`AllQueryAttentionKnockout` **does not write `n_prefill_edits`**, but
`LIVENESS_REQUIREMENT["legacy_all_query"]` requires it > 0, and `scoped_liveness_violations` reads
`stats.get(key, 0)` — so **a key the legacy hook never wrote is indistinguishable from a real zero, and
every legacy arm would have been reported as dead at prefill.** A *fabricated liveness failure* is as
useless as a fabricated pass, and both are silent. It is derived instead, in one place, from the
invariant both classes share: `n_edits == n_prefill_edits + n_decode_edits`.

**I did not take that invariant on trust.** Driven independently through the repo's own toy harness on
three geometries (1 prefill + n decode steps):

| layers / seq / decode steps | legacy `n_edits` | legacy `n_decode_edits` | derived `n_prefill_edits` | scoped `n_prefill_edits` |
|---|---|---|---|---|
| 2 / 8 / 3 | 34 | 12 | **22** | **22** ✅ |
| 3 / 12 / 5 | 123 | 45 | **78** | **78** ✅ |
| 1 / 6 / 1 | 5 | 1 | **4** | **4** ✅ |

`n_edits` and `n_decode_edits` are identical between the two classes on all three, the gate **passes**
the derived legacy stats, and — the check that matters — it still **catches** a hand-injected dead
decode hook (`n_decode_edits = 0` → violation). **The legacy liveness verdict is sound and is not
fabricated in either direction.**

**Tests:** 52 new synthetic tests reusing the existing `ToyModel` harness rather than re-implementing
it, including legacy **byte-identity** at prefill and every decode step, zero-decode-edits for both
prefill-only modes, `decode_only` leaving the prefill mask `torch.equal` to baseline, and the
**disjointness** test that makes the decomposition a decomposition:
`query_prefill_only` and `demo_processing_only` edit **disjoint** query-row sets whose union is a subset
of legacy's. Both absolute-vs-cache-local coordinate-confusion directions are tested.
**Verified by me, serially: 194 passed** across the 10 new and affected files.

⚠ **What this is NOT.** No arm has run, no GPU has been used, and nothing here says anything about
behaviour. The next step is PR-1's 8-row liveness smoke, and **no scientific arm runs until every mode
fires exactly as designed.**

---

### ★★★ R-4 (01:16) — **THE INCOMPLETE-RUN PROBLEM IS 12× BIGGER THAN THE AUDIT FOUND: 62 directories, not 5 — and one of them is my own.**

**Artifact:** `outputs/boombness/EXCLUDED_RUNS.json` (schema `EXCLUDED_RUNS/1`, tracked).
**Producing script:** `src/boombness/excluded_runs.py`.

The Part-II audit found **5 of 12** incomplete dirs under `crossbank_knockout_test/`. Scanning **every**
experiment directory instead:

| experiment | dirs lacking `DONE.json` |
|---|---|
| `judge` | **31** |
| `score_behavior` | **21** |
| `crossbank_knockout_test` | 5 |
| `extract_boombness` | 3 |
| `retrieval_strength` | 1 |
| `rederive_crossbank` | **1 — mine** |
| **total** | **62** |

By reason: **28** `no_done_json`, **27** `empty_skeleton`, **7** `aborted`. **33 carry partial results**
— the dangerous shape, because a partial dir flows through a `newest()`-style lookup and produces a
plausible number. **Nothing is marked `safe_to_delete`; nothing was deleted.** The skeletons are
evidence of a debugging sequence.

**The scanner immediately earned its keep by catching my own debris:**
`rederive_crossbank/rederive10_20260825_002905_2199605` — the run that died on the repo's
`FailureLedger` guard while I was building R-1 — is classified `no_done_json`, `has_partial_results:
true`, `superseded_by: rederive10_20260825_002934_2201570`. **A glob over that experiment directory
would have had two candidates and no way to tell them apart.**

---

### ⛔⛔ R-2 / C-1 (00:29) — **THE HEADLINE DIRECTION IS ONE DEMONSTRATION CORPUS. Drop the bomb pool and the prompt-level effect is p = 0.092.** First correction of this phase, and it is to the claim the whole phase inherits.

**Artifact:** `outputs/boombness/rederive_crossbank/rederive10_20260825_002934_2201570/rederive_crossbank.json`
**Producing script:** `src/boombness/rederive_crossbank.py` (new, this phase)
**Command:** see §B9. Threshold 0.50, 10 populations, 143 discordant comparisons.

The surviving inherited claim is *"the direction is well supported — 113 down against 30 up,
p = 1.577e-12."* **Decomposed by demonstration pool, that p is one corpus:**

| demonstration pool | concept | down / up | **exact two-sided binomial p** |
|---|---|---|---|
| **`b5e399712b996b7d`** | **bomb** | **81 / 11** | **2.50151e-14** |
| `5d3080f60af987c6` | knife | 15 / 7 | **0.133801** |
| `79e93dbb2b65c820` | gun | 17 / 12 | **0.458258** |

| leave-one-pool-out | down / up | p |
|---|---|---|
| drop knife | 98 / 23 | 3.23986e-12 |
| drop gun | 96 / 18 | 4.72143e-14 |
| **drop bomb** | **32 / 19** | **0.0919145** |

> **The effect is significant on one of three demonstration corpora and null on the other two.**
> That is a materially different claim from *"113 down against 30 up over 10 populations"*, and it is
> the claim the artifact supports.

⚠ **And `pool` is perfectly confounded with target CONCEPT here** — b5e3 = bomb, 5d30 = knife,
79e9 = gun. So "three independent demonstration pools" and "three target concepts" are **the same
factor**. The pool main effect in the ANOVA below is also a concept main effect and cannot be
separated at k=3. Nothing in the previous phase says this.

**Two further composition defects in the same statistic, both confirmed:**

* **The n is inflated by design-slot reuse.** The 143 discordant comparisons come from only
  **67 distinct `prompt_id`s** of 96 — the ten populations are the same 96 design slots with different
  lexical fill, so one slot can contribute up to 10 comparisons. The binomial assumes prompt
  independence, which this violates by construction.
* **The both-arms-EOS control is not a 10-population control.** It reproduces numerically
  (**30 down / 1 up, p = 2.9802322387695312e-08**) but **5 of the 10 populations contribute zero
  both-EOS discordant rows**: `Q|window_knife`, `L|ticket_bomb`, `L|button_knife`, `L|window_knife`,
  `L|basket_gun`. Truncation is heavily asymmetric on Llama, so the control is carried by the same
  populations as the effect.

**Status:** the LIVE ledger's direction row is amended, not deleted. Direction still holds *as a
direction*; what is withdrawn is the implication that 10 populations, 5 banks and 3 pools are
independent support for it.

---

### ★★★★ R-1 (00:29) — **PHASE-0 §2.1 SATISFIED: an independent re-derivation reproduces prev-C-18 to the digit, including the number C-18 could not have taken from the repo's own table.**

**Artifact:** as R-2 above. **The path is genuinely independent** — `rederive_crossbank.py` imports
`common` only (for `RunDir` / `FailureLedger`) and does its own arithmetic; it never imports
`crossbank_knockout_test`. Agreement is therefore evidence, not tautology.

| quantity | prev-C-18 | **this re-derivation** |
|---|---|---|
| all 10 populations are the same 96 `prompt_id`s | asserted | **CONFIRMED** — all 45 pairwise intersections = 96, union = 96 |
| distinct demonstration pools | 3 | **3** (proved from bank `_meta.pools_sha16`, not bank names) |
| pool main effect | SS 0.10102, df 2, 30.2 % | **0.10101996528, df 2, 30.207657 %** |
| domain main effect | SS 0.10655, df 5, 31.9 % | **0.10655381944, df 5, 31.862427 %** |
| interaction | SS 0.12684, 37.9 % | **0.12684461806, df 10, 37.929916 %** |
| **share that is double-counted main effects** | 62.1 % | **62.0701 %** |
| k=18 crossed cells *(the retracted unit)* | [−0.1461, −0.0066] | **[−0.1461364242, −0.0066413536]**, excludes 0 |
| k=3 pool marginal | [−0.3043, +0.1516] | **[−0.3043121512, +0.1515343734]**, includes 0 |
| k=6 domain marginal | [−0.1649, +0.0121] | **[−0.1648382480, +0.0120604702]**, includes 0 |
| crossed random-effects interval | [−0.2796, +0.1268] at df 2.53 | **[−0.2795835881, +0.1268058104] at df 2.5294593771** |

**One thing this pins that was previously unverifiable.** The crossed random-effects interval
reproduces *only* with a real t distribution (`scipy.stats.t.ppf`); the repo's own shipped `_T`
interpolation gives t = 3.7095 at df 2.53 and hence [−0.28901, +0.13623]. **So prev-C-18's published
number did not come from the tool's table**, and if that interval is ever moved into an artifact the
two paths would disagree by 0.0095 on the lower limit. Recorded so the discrepancy is a known
convention rather than a future correction.

⚠ **An ambiguity in "the domain marginal" that someone must resolve.** There are two of them, and the
previous phase quotes both. **Pool-balanced** (mean the 3 pool cells per domain, then the 6 domains):
mean **−0.0763888889**, CI **[−0.1648382480, +0.0120604702]** — what this artifact reports.
**Population-weighted** (mean the 10 population cells per domain): mean **−0.0865**, CI upper
**+0.0108** — what prev-R-BE reports. **Both include zero, so the conclusion is identical**, but the
numbers differ and adjacent tables in the previous log quote the k=6 CI from one and the k=6 p from the
other. **This phase uses the pool-balanced version and says so**, because pool is the independence
axis C-11 established.

**Judge hygiene, checked rather than assumed:** `judge_status == "ok"` on all 96 rows of all 20 judge
dirs; zero null `strongreject_score`; the `FailureLedger` records 0 unpaired prompt_ids, 0 null scores,
0 missing `stop_reason` across all 10 populations (960 paired rows).

## B6. CORRECTIONS / RETRACTIONS

*(`C-` ids, newest first. This phase's numbering starts at C-1 and is namespaced to this file; the
previous phase's C-1…C-18 are referenced by name, e.g. "prev-C-18".)*

### 🏆🏆🏆 R-12 (07:40) — **OUTCOME B REPLICATES ON QWEN3-14B, and the control contrast makes it sharper than PR-5 asked for: only the arms that touch the demonstrations' OWN processing beat their matched control. Both response-side arms are EXACTLY equal to it.**

**Artifact:** `outputs/boombness/phase1_decomposition/q1dec_20260825_073814_2825688/phase1_decomposition.json`
**Judging:** job **779754**, all 8 arms in ONE pinned session, `ALL DONE`, every arm `verified (96 rows)`.
Qwen3-14B, band **L7–17**, baseline ASR **0.1771** (healthy headroom, matching prev-R-AA's 0.1875).

| arm | ASR | **Δ** | down/up | refused | median chars | domain p | floor |
|---|---|---|---|---|---|---|---|
| **`legacy_all_query`** | 0.0104 | **−0.1667** | 17/1 | 0.000 | 319 | 0.0625 | 0.0625 |
| **`demo_processing_only`** | 0.0208 | **−0.1562** | 17/2 | **0.156** | 805 | 0.3750 | 0.0625 |
| `response_query_only` | 0.1042 | **−0.0729** | 11/4 | 0.000 | 324 | 0.1250 | 0.1250 |
| `query_prefill_only` | 0.1042 | **−0.0729** | 10/3 | 0.000 | 381 | 0.1250 | 0.1250 |
| `decode_only` | 0.1458 | −0.0312 | 7/4 | 0.010 | 523 | 0.2500 | 0.2500 |
| `late_depth` (25–39) | 0.1146 | −0.0625 | 9/3 | 0.010 | 586 | 0.2500 | 0.2500 |
| `late_count` (25–35, 11 blocks) | 0.1042 | −0.0729 | 9/2 | 0.010 | 598 | 0.1250 | 0.1250 |

#### 🚦 PR-5's three conditions, scored exactly as written before these arms were submitted

| # | condition | value | verdict |
|---|---|---|---|
| 1 | `demoproc` larger than `respq` by > 0.0417 | 0.1562 − 0.0729 = **+0.0833** | ✅ **HOLDS** |
| 2 | primary fails equivalence AND `respq` < half of legacy | gap **0.0937**; frac **0.438** | ✅ **HOLDS** |
| 3 | `query_prefill_only` does NOT suppress (≥ −0.0521) | **−0.0729** | ⛔ **FAILS** |

**Conditions 1 and 2 hold, so the core of Outcome B replicates across two model families.**
Condition 3 fails, and PR-5 already wrote what that means: *"the Llama +0.0625 is model-specific and
must be reported as such rather than as a general finding about query-side access."* **It is.**

#### 🎯 But the matched control turns condition 3 into something much stronger

Subtracting each arm's **layer-count-matched** late control (`late_count`, 11 blocks, the arm that
exists only because C-3e caught the 12-vs-9 mismatch on Llama):

| arm | Δ | **Δ − late_count** |
|---|---|---|
| `legacy_all_query` | −0.1667 | **−0.09375 (−15/160)** |
| `demo_processing_only` | −0.1562 | **−0.0833** |
| `response_query_only` | −0.0729 | **+0.0000** |
| `query_prefill_only` | −0.0729 | **+0.0000** |
| `decode_only` | −0.0312 | +0.0417 |

> **Both response-side arms are EXACTLY equal to the late-layer control — to the prompt.** Their
> −0.0729 is not band-specific suppression at all: doing the same thing at layers 25–35 does the same
> thing. **Only `legacy_all_query` and `demo_processing_only` — the two arms that touch the
> demonstrations' own processing — exceed their matched control.**

**So `query_prefill_only`'s Qwen3 "suppression" is entirely non-specific, and the honest cross-model
statement is stronger than PR-5 anticipated:** on both models, *nothing that scopes the intervention to
the response side produces band-specific suppression* — on Llama it moved the wrong way, on Qwen3 it
matches its own control.

#### The refusal signature replicates too, and the length collapse does NOT

`demo_processing_only` refuses on **0.156** of rows against `legacy`'s **0.000** — the same 20×-ish
elevation R-10 found on Llama (0.208 vs 0.010). **But its Llama length collapse does not replicate**:
median 805 chars with **1** row under 200, against Llama's 20. **So the collapse was Llama-specific
while the refusal elevation is cross-model** — which is evidence that the refusal, not the truncation,
is the arm's real signature. *(C-4 flagged the collapse as a confound; R-10 showed the effect survived
conditioning; this shows the confound itself does not cross models.)*

#### ⛔ Statistics, stated plainly

`legacy_all_query` reaches **p = 0.0625, exactly its floor** (5 informative domains, all negative).
Everything else is at or above its own floor. **As on Llama, no arm goes below the design's attainable
floor**, and PR-3 predicted that. The magnitudes, their ordering, and the arm-minus-control contrast
are the quotable content.

---

### ★★★★ R-11 (06:40) — **THE QWEN3 SMOKE PASSES, and it independently CONFIRMS C-3b's corrected mechanism on a second model — a prediction the discarded explanation could not have made.**

**Artifact:** `outputs/boombness/scoped_smoke_verdict/s2verdict_20260825_063809_2764586/scoped_smoke_verdict.json`
— **PASS, 5 arms, 0 failures.** Jobs 779733–779738, all COMPLETED `0:0`, band **L7–17**,
`--enable-thinking false`.

| arm | prefill edits | decode edits | min forwards where FORBIDDEN | gens changed |
|---|---|---|---|---|
| `legacy_all_query` | 324 335 | 368 247 | — | 8/8 |
| `query_prefill_only` | 130 900 | **0** | `decode_forward: 605` | 8/8 |
| `decode_only` | **0** | 419 958 | **`prefill_forward: 11`** | 8/8 |
| `response_query_only` | 130 900 | 442 475 | — | 8/8 |
| `demo_processing_only` | 188 760 | **0** | `decode_forward: 957` | 8/8 |

**`decode_only`'s `prefill_forward = 11`** is the depth mapping doing its job: **11 band layers on
Qwen3's 40 blocks against 9 on Llama's 32.** The hook was called at every one and edited nothing.

#### 🎯 C-3b's corrected mechanism predicted the Qwen3 slack, and the discarded one could not

The 4-hour review corrected my explanation of the prefill slack: it is **not** "the chat template and
preamble" (which contribute exactly zero, being unable to attend to a demo key that comes after them)
but **one inter-span seam token per prompt**, i.e. `n_layers × Σ n_demo_positions × 1`.

**That is a prediction, and it holds across models on the same 8 prompts:**

| model | band layers | slack | slack ÷ layers |
|---|---|---|---|
| Llama-3.1-8B | 9 | 3 825 | **425** |
| **Qwen3-14B** | **11** | **4 675** | **425** |

**Identical `Σ n_demo_positions = 425`, and the slack scales exactly with layer count.** The
explanation I originally published predicts nothing and would not scale this way. **A corrected
mechanism that then predicts a number on a different model is worth more than the correction itself**,
and it is recorded here rather than left in the correction that produced it.

Subset check holds on Qwen3 too: `130 900 + 188 760 = 319 660 ≤ 324 335`, slack 4 675.

---

### 🔬 P1.4 LAUNCHED (06:41) — the Qwen3 8-arm replication at n = 96

Jobs **779742–779749**, band **L7–17**, `--expect-n 96`, to be judged in ONE pinned session.
**Read against PR-5's three conditions, which were fixed before these were submitted.**

| job | arm | band |
|---|---|---|
| 779742 | `A_baseline` | — |
| 779743 | `C_legacy_all_query` | 7–17 |
| **779744** | **`C_response_query_only`** | 7–17 |
| 779745 | `C_query_prefill_only` | 7–17 |
| 779746 | `C_decode_only` | 7–17 |
| 779747 | `C_demo_processing_only` | 7–17 |
| 779748 | `D_late_depth` | **25–39** — depth-matched to Llama's 20–31 (0.625–1.0) |
| 779749 | `D_late_count` | **25–35** — **layer-count** matched to the arm's 11 blocks |

**Two late controls again, for the reason C-3e recorded on Llama:** a depth-matched late band is not
layer-count matched, and the Llama pair differed by exactly 12/9. Running both here means the Qwen3
comparison is matched on each axis without having to choose which one matters after seeing the result.

---

### 🏆🏆🏆 R-10 (05:41) — **PHASE 1 RESULT: OUTCOME B. The causal path is NOT response-time retrieval. Corrupting the demonstrations' OWN encoding carries 92 % of the effect; masking the response's access to them carries 46 %; and masking the final query's prefill access moves ASR the WRONG WAY.**

**Artifact:** `outputs/boombness/phase1_decomposition/p1dec_final_20260825_054056_2706137/phase1_decomposition.json`
**Producing script:** `src/boombness/phase1_decomposition.py`. **Judging:** job **779712**, all 8 arms in
ONE session, `ALL DONE`, every arm `verified (96 rows)`, backend **pinned** — `judge_model_used =
openai/gpt-4o-mini` on **768 of 768 rows**, and `judge_model_pinned` likewise. **This is the first
result in the project whose judge is a single recorded model rather than an unrecorded fallthrough.**

Llama-3.1-8B, band **L6–14**, n = 96, baseline ASR **0.1667**, threshold 0.5.

| arm | ASR | **Δ** | down/up | refused | median chars | frac at cap | rows <200ch | uniq texts | domain p | floor |
|---|---|---|---|---|---|---|---|---|---|---|
| **`legacy_all_query`** | 0.0312 | **−0.1354** | 16/3 | 0.010 | 771 | 0.552 | 1 | 96/96 | 0.3750 | 0.0625 |
| **`demo_processing_only`** | 0.0417 | **−0.1250** | 15/3 | **0.208** | 776 | 0.719 | **20** | 86/96 | 0.1250 | 0.1250 |
| **`response_query_only`** | 0.1042 | **−0.0625** | 14/8 | 0.021 | 773 | 0.490 | 2 | 96/96 | 0.6250 | 0.1250 |
| `decode_only` | 0.1771 | **+0.0104** | 8/9 | 0.031 | 788 | 0.635 | 3 | 96/96 | 1.0000 | 0.0625 |
| **`query_prefill_only`** | 0.2292 | **+0.0625** | 11/17 | 0.031 | 782 | 0.500 | 3 | 96/96 | 0.6250 | 0.1250 |
| `late` control (20–31, 12 blocks) | 0.1979 | +0.0312 | 9/12 | 0.042 | 792 | 0.542 | 4 | 95/96 | 0.6250 | 0.1250 |
| `late9` control (20–28, 9 blocks) | 0.2188 | +0.0521 | 8/13 | 0.042 | 806 | 0.594 | 4 | 94/96 | 0.6875 | 0.0312 |

#### 🚦 The pre-registered primary comparison FAILS equivalence

```
delta(response_query_only) = -0.0625      delta(legacy_all_query) = -0.1354
|gap| = 0.0729   >   PR-3 margin 0.0417   ->  NOT equivalent
response_query_only recovers 46.2 % of the legacy arm
```

**Outcome A required `response_query_only` ≈ legacy AND `demo_processing_only` weak. Both halves
fail.** `demo_processing_only` is not weak — it is **92.3 %** of legacy — and `response_query_only` is
less than half. **This is Outcome B**, the branch PR-1 wrote as *"⛔ retract the 'generated answer
retrieval' wording; the result becomes: disrupting the demonstrations' internal representation
suppresses the attack."*

> **The wording this project has used loosely — *"generated answer tokens need to retrieve information
> from the demonstrations"* — is not supported. The scoped decomposition says the opposite: most of the
> effect is in what the demonstrations do to THEMSELVES during prefill.**

#### ⚠ And the arm that moves the wrong way is the sharpest single line

**`query_prefill_only` gives Δ = +0.0625** — blocking the **final query's** prefill access to the
demonstrations makes the attack **MORE** successful, by 6 prompts of 96, with 11 down against **17 up**.
Its per-domain pattern is genuinely mixed (`farm_storage` +0.1875, `instructional` +0.1875,
`lab_safety` +0.125, `city_bridge` −0.125), i.e. not one domain driving it. **Combined with
`decode_only`'s +0.0104, neither half of "the response computation reads the demonstrations" suppresses
anything.**

#### ✅ PR-4's length check: NOT a truncation artifact — for any arm

Every arm's Δ is **stable** across the length-conditioned sweep, which is the check prev-Gate-E7 failed
(where `d_surface:add` went to **exactly 0.0000** at T = 80):

| arm | T=0 | T=80 | T=200 | T=400 |
|---|---|---|---|---|
| `demo_processing_only` | −0.1250 | −0.1183 | **−0.1200** (n=75) | −0.1200 |
| `legacy_all_query` | −0.1354 | −0.1354 | −0.1398 | −0.1398 |
| `response_query_only` | −0.0625 | −0.0526 | −0.0543 | −0.0549 |
| `query_prefill_only` | +0.0625 | +0.0625 | +0.0769 | +0.0778 |

**`demo_processing_only`'s effect survives conditioning**, so C-4's collapse concern is answered: the
20 short rows are real but they are **not** what produces the ASR drop. ⚠ PR-4's collider caveat still
travels with this — conditioning on a post-treatment variable cannot *prove* an effect genuine; it can
only show the effect is not *made of* the truncated rows. **Both views are reported; neither alone is
the headline.**

#### ⚠ But `demo_processing_only` suppresses through REFUSAL, and that changes what it means

| arm | refusal rate |
|---|---|
| `legacy_all_query` | 0.010 |
| `response_query_only` | 0.021 |
| **`demo_processing_only`** | **0.208** |

**A 20× increase over the legacy arm, and 10× over the baseline's own refusal.** So the winning arm does
not suppress the attack the way the legacy arm does. **Corrupting the demonstrations' own encoding makes
the model REFUSE; masking the response's access to them does not.** That is a mechanistic difference the
ASR column alone hides, and it is why Phase 2's semantic-binding probe and Phase 2B's phenotype
instrument are now the decisive next measurements rather than optional ones.

#### ⛔ What is NOT established — the statistics, stated plainly

**No arm reaches significance at the pre-registered unit.** Domain-clustered sign tests:
`legacy` p = 0.3750, `demo_processing_only` **p = 0.1250 — exactly its floor**, `response_query_only`
p = 0.6250, `decode_only` p = 1.0000. **PR-3 predicted this**: with 6 domains and `lab_safety`
frequently netting zero, the attainable floor is 0.0625–0.1250 and **nothing can go below it however
large the effect**. The magnitudes and their **ordering** are the quotable content; the p-values are
not, and are reported here only with their floors attached.

⚠ **Single model, single band, single bank, n = 96, one judging session.** The Qwen3 replication is the
next experiment. **Outcome B is a claim about Llama-3.1-8B on this bank until it replicates.**

---

### R-60 (02:20) — **PR-25 gate 4 PASSES: the pool-B bank keeps enough attack. All four gates clear; the sweep is submitted. `n=4` is again exactly ON the threshold.**

| Qwen3 bank | total | n=1 | n=2 | **n=4** | **n=8** |
|---|---|---|---|---|---|
| pool A (`longpreQ14`) | 17/160 | 3 | 3 | **4** | **7** |
| **pool B (`longpreQ14B`)** | **12/160 = 0.0750** | 0 | 2 | **4** | **6** |

**Gate 4's rule — ≥4 baseline attack rows at n=4 and n=8 — is met (4 and 6).**

⚠ **`n = 4` sits at exactly 4 rows for the second time**, as it did on pool A (R-56). PR-25 requires
**both** doses, so a single row moving in the judge could take that cell under the threshold and turn
a confirmation into a decline. **Said before the arms run, not after.**

⚠ **Pool B carries less attack overall than pool A** (12/160 vs 17/160), and **`n=1` has zero
baseline attacks** — that dose is vacuous here and was never part of the claim. **The 5-row
difference is inside the 8.3-row margin, so no cross-pool magnitude claim is made**; it is recorded
because it is the power the test has to work with.

**All four gates now clear:** `--strict` 0 violations · audit 0 alignment violations · **Qwen3
`match_ratio` min 1.000 at every dose** · power 4 and 6.

**Submitted:** `q16_demoproc` and `q16_matched_d1`, two at a time per the NFS-contention lesson;
`d2`/`d3` follow when these clear. **PR-23's conditions apply unchanged — a new pool licenses no new
thresholds — and the three draws must be independent by seed AND by generation hash (C-17).**

---

### R-59 (01:45) — **PR-25 gates 1-3 PASS on pool B. And the `deficit` field I added yesterday turned out to be a conservative BOUND, not a per-row test — clarified before it could be misread.**

| gate | result |
|---|---|
| 1 · `--strict` | `families checked=560 violations=0`, duplicates 0 |
| 2 · `tokenization_audit` (784309) | `rows ok=4560 bad=0 ambiguous=0`, **0 alignment violations** |
| 3 · **Qwen3 feasibility** (784310) | **`match_ratio` min 1.000 at ALL four doses**, `feasible=True` |
| — | bank `b2903479258a0f68`, 4560 rows, **differs from the pool-A bank** |

**Gate 3 was the one expected to be at risk** — `n_preamble = 14` cleared pool A by a single token
(129 vs 128), and pool B has different demo lengths. **It passed with room: pool min 122 against the
longest row's own pool, `match_ratio_min` 1.000 everywhere.** No fallback to 16 needed.

#### ⚠ A metric of mine that reads like a contradiction, and is not

Pool B at `n_examples = 8` reports **`deficit = 10` while `match_ratio_min = 1.000`.** That looks
inconsistent and is not: **`pool_deficit_vs_max_demo` compares the LONGEST demo block at the dose
against the SMALLEST pool at the dose — and those are usually DIFFERENT ROWS.** The 132-token demo
row has a pool larger than 122; the row with the 122-token pool has a shorter demo. **The bound is
conservative, not a per-row diagnosis.**

**Fixed before it could mislead anyone, including me:** the field now carries that explanation at its
definition, and a genuinely per-row companion — **`n_rows_demo_exceeds_own_pool`** — is emitted
alongside it. **`match_ratio_min` remains the criterion; the deficit is for seeing how close a bank is
to trouble.** I introduced this field one day ago while diagnosing C-18 and had already begun reading
it as if it were the test.

**Gate 4 (power) is running:** `q16A`, the pool-B baseline. **≥4 baseline attack rows at n=4 AND n=8
or the branch stops** — the rule that declined R-52 and that R-56 flagged as marginal at exactly 4.

---

### PR-25 (01:15) — **Pre-registered: replicate C7 on pool B — an independent demonstration pool, the same move that took C1 from one setting to three.**

C7 (R-58) is **one model, one pool**. **Every claim in this phase that survived was replicated on a
second independent setting** — C1 across two model families and two pools (R-29), C9 across a 2×2
(R-38). **C7 has not been, and it is the phase's newest and most fought-over result.**

**Llama is not the vehicle** — R-52 established that the preamble costs Llama its attack, and R-58's
Qwen3 result is single-model precisely because of that. **The available independent axis is the
demonstration pool**: `demo_pools_d10_poolB.json`, whose 40 pools share **0 of 40 sentence sets** with
pool A (R-28).

**Gates, in order, each able to stop this before the next GPU hour is spent:**
1. **`--strict`** on the pool-B `main_longpre --n-preamble 14` bank → 0 violations.
2. **`tokenization_audit`** → 0 alignment violations.
3. **Qwen3 feasibility** (`control_feasibility --model Qwen/Qwen3-14B`) → **`match_ratio` min 1.000 at
   every dose.** ⚠ **14 was chosen with one token of headroom on pool A (129 vs 128); a different pool
   has different demo lengths, so this gate may fail and 16 is the recorded fallback** — selected on
   feasibility alone, never on the attack rate.
4. **Power**: one baseline arm, then **≥4 baseline attack rows at n=4 AND n=8**, or the branch stops.

**Only if all four pass** do the four intervention arms run.

**⛔ Conditions are PR-23's, unchanged. A new pool does not license new thresholds.** CONFIRMS only if
all three hold at `n_examples` **4 and 8**: `demoproc` clears ±0.0521; each of three independent
matched controls stays within it; separation exceeds 0.0417.

**REFUTED if** the matched controls remove attack comparably **on a powered population** — which would
mean R-58 was pool-specific, and **C7 would revert to unresolved rather than staying confirmed on one
pool.** Stated before the bank exists.

**⛔ Also pre-committed:** the three draws must be **genuinely independent** — distinct seeds **and**
distinct generation hashes, per C-17, because that check is what stops a duplicated directory
masquerading as a draw.

---

### 🏆🏆🏆 R-58 (00:55) — **PR-23 CONFIRMS. C7 — the phase's only unresolved claim — is RESOLVED on Qwen3: masking the demonstration positions removes the attack because they are the DEMONSTRATIONS, and a count-matched mask of the same size elsewhere does not.**

**Artifacts:** arms `q15*` (783849, 783903, 783904, 783945, 783946); judging `q15j_*` (784128).
**Provenance 800/800**, hash joins **800/800**.
**Preconditions, all met and all verified from the runs themselves:** `scope_live = 1.0` with no
violations on every intervention arm; **`match_ratio` min 1.000 on all 480 control rows**; and the
three draws are **genuinely independent** — distinct seeds (28180602 / 36100379 / 44020156) and
**3/3 distinct generation hashes**, which is C-17's rule that directories are not draws.

| dose | baseline | `demoproc` | d1 | d2 | d3 | ctrl mean |
|---|---|---|---|---|---|---|
| 1 | 2/40 | −0.0250 | +0.0250 | +0.0000 | +0.0000 | +0.0083 |
| 2 | 2/40 | +0.0000 | +0.0250 | +0.0250 | +0.0750 | +0.0417 |
| **4** | **5/40** | **−0.1250** | −0.0250 | −0.0500 | −0.0500 | −0.0417 |
| **8** | **7/40** | **−0.1250** | −0.0500 | +0.0500 | +0.0250 | +0.0083 |

**In rows, which is how DR-5 requires this be quoted:**

| dose | demoproc removed | the three matched controls removed |
|---|---|---|
| **4** | **5 of 5 attacks** | **1, 2, 2** |
| **8** | **5 of 7 attacks** | **2, −2, −1** |

**All three PR-23 conditions hold at BOTH decisive doses:**
1. `demoproc` removes attack — **−0.1250 at each**, against a 0.0521 margin.
2. Every matched control stays inside ±0.0521 — **max |0.0500|** at both doses.
3. They separate — **0.0833 (2.0×)** at n=4 and **0.1333 (3.2×)** at n=8, against a 0.0417 margin.

> **Masking N demonstration positions kills the attack. Masking the same N positions drawn from
> elsewhere in the same prompt does not. The effect is about WHICH positions they are.**

#### Why this took eleven steps, and why the earlier failures were not this

C7 has been the phase's open wound since R-24. **Every prior attempt failed for a reason that was
recorded and then fixed rather than argued around:** the control was not constructible (R-24/R-25);
one dose came for free from the capped policy (R-26); my first bank fix grew the demonstration block
instead of the pool (R-46); the requirement was quantified (R-48) and built (R-49); Llama had the
control but lost the attack (R-50/R-52); Qwen3 was found to keep its attack (R-54); the Llama
feasibility number did not transfer (C-18); the bank was re-derived on the right tokenizer (R-55);
and the live pre-flight confirmed it (R-57). **The claim did not change once. The instrument did.**

#### ⚠ What this is NOT

* **Single-model.** Llama's version was **declined for power**, never refuted — R-52 stands, and
  **C7 is confirmed on Qwen3 only.**
* **Small counts.** 5 and 7 baseline attacks. `demoproc`'s effect is **5 rows against a 2.1-row
  margin** at both doses — 2.4×, comparable to C12's thinness.
* **Not a claim that the controls are inert.** They removed 1-2 rows at n=4 and one *added* 2 at n=8.
  **They are within margin, which is what was pre-registered — not zero.**
* **n=1 and n=2 carry 2 baseline attacks each and say nothing**; they were never the claim.

---

### ✅ R-57 (00:12) — **C-18's loop is CLOSED: the live Qwen3 pre-flight on `longpreQ14` reports `match_ratio` 1.000 at every dose, min and mean, with zero infeasible rows.**

The failure mode that killed PR-23 was a Qwen3 arm refusing at pre-flight. **The same arm on the
repaired bank reports:**

| dose | n | min | mean | rows below 1.0 |
|---|---|---|---|---|
| 1 | 40 | **1.000** | 1.000 | **0** |
| 2 | 40 | **1.000** | 1.000 | **0** |
| 4 | 40 | **1.000** | 1.000 | **0** |
| **8** | 40 | **1.000** | 1.000 | **0** |

`infeasible_control: 0`. **Refusals: 0.**

**This is the validation that matters, and it is not the one I already had.** R-55 predicted
feasibility from the **CPU instrument**; this is the **live arm's own pre-flight**, on the real
tokenizer, in the real run — the exact measurement whose disagreement produced C-18. **The
one-token headroom (pool min 129 vs demo max 128) held on all 160 rows.**

**PR-23's precondition is therefore met for `d1`** — and it will be read the same way for `d2` and
`d3` before any result is computed, since PR-23 requires it **on every control row of every draw**,
not on one arm.

⚠ **Still nothing read.** The arm has passed its pre-flight; it has not finished generating. **A
precondition passing is not a result**, and the C7 verdict needs all three draws plus judging in one
window.

---

### 🔎 DR-9 (23:45, DEEP REVIEW) — **1422/0. Found an UNCOMMITTED instrument change that R-55's selection table already quoted — caught only because the C-2 check is now scoped.**

**Suite:** `1419 passed, 7 skipped, 0 failed` plus the three bank-regeneration tests run separately
(**3 passed**) — **1422 total, 0 failures.** The bank tests are deselected from the main run because
they regenerate two full banks and pushed the suite past a 10-minute budget; **they are not skipped,
they are run in their own invocation.**

#### 🔴 The find: an instrument change that was never committed

`src/boombness/control_feasibility.py` was **modified but uncommitted** — the `max_n_demo`,
`min_drawable_pool` and `pool_deficit_vs_max_demo` fields added while measuring the Qwen3 deficit.
**R-55's selection table quotes those numbers.** So the working tree emitted them while **the
committed instrument did not**, and anyone reproducing from the repo would have got an artifact
missing the fields the decision was justified by.

**It was caught only because the C-2 status check is now scoped to my own paths** (18:45). Against
the unscoped check it would have sat invisible under the concurrent writer's 1,187-line diff.
**Narrowing that check three ticks ago paid for itself here.** Committed at `cf4745d9`.

#### Provenance sweep

**23 banks, all tracked, none untracked.** The three this phase created carry distinct hashes —
`longctx 4d888074`, `longpre d163e28c`, `longpre10 87343411`, `longpreQ14 a12427b9` — and `d10`
still hashes `368566acecdc350f`, matching C-10's recorded value from two days ago.

⚠ **One incidental observation, not mine to fix:** `boombness_prompt_bank_button.jsonl` and
`boombness_prompt_bank_button_bomb.jsonl` are **byte-identical** (`95a3a8017f9ab180`). They predate
this phase and nothing here joins to them. **Recorded, not touched** — a duplicate in another
sprint's artifacts is that sprint's to reconcile.

**My paths are clean; nothing unpushed.**

---

### R-56 (23:20) — **Power check on `longpreQ14` BEFORE spending the sweep: PROCEED, but `n_examples = 4` sits exactly ON PR-23's threshold.**

C-18 was caused by assuming a bank property measured on another model. **So the 14-sentence bank was
not assumed to retain the attack — it was measured, with one baseline arm, before any intervention
arm was submitted.** Smoke before sweep.

| Qwen3 bank | total | n=1 | n=2 | **n=4** | **n=8** |
|---|---|---|---|---|---|
| d10 | 21/160 = 0.1313 | 3 | 3 | **7** | **8** |
| longpre10 (10) | 23/160 = 0.1437 | 3 | 5 | **6** | **9** |
| **longpreQ14 (14)** | **17/160 = 0.1062** | 3 | 3 | **4** | **7** |

**PR-23's rule — ≥4 baseline attack rows per decisive dose — is met: `n=4` has 4, `n=8` has 7.
Proceeding.**

⚠ **But `n = 4` is exactly ON the threshold, not above it**, and that is the same position PR-19's
Llama `n=4` cell occupied before it failed. **PR-23 requires BOTH doses**, so if that cell is noisy
the test can fail for power reasons again rather than for scientific ones. **Stated now, so that
outcome is not later described as a refutation.**

⚠ **The longer preamble does cost some attack on Qwen3** — 17/160 against d10's 21/160 — **but 4 rows
is inside the 8.3-row margin, so this is not a contradiction of R-54's "no measured cost"**; it is the
same null, measured on a longer preamble. **No cross-bank magnitude claim is made from it.**

**Now submitted:** `q15_demoproc` and `q15_matched_d1` on `longpreQ14`, two at a time per the
NFS-contention lesson. **PR-23's conditions and preconditions are unchanged.**

**Orphaned by C-18 and recorded so it is not silently reused:** `q14_demoproc` is a complete, valid
Qwen3 `demo_processing_only` arm on `longpre10` (160 rows, twice, byte-identical) — **but its controls
cannot be built on that bank, so it cannot serve PR-23.** It is not deleted and it is not evidence for
anything on its own.

---

### 🔧 R-55 (22:30) — **PR-24 resolved: `n_preamble = 14` is the Qwen3 minimum. It clears by ONE token, and the parameter is now explicit instead of hardcoded.**

| `n_preamble` (Qwen3 tokenizer) | pool MIN | demo MAX @ n=8 | deficit | feasible everywhere? |
|---|---|---|---|---|
| 10 (Llama's pick) | 112 | 128 | **16** | ❌ |
| 12 | 113 | 128 | **15** | ❌ |
| **14** | **129** | 128 | **0** | ✅ **selected** |
| 16 | 151 | 128 | 0 | ✅ but 22 tokens of surplus |

**Selected on feasibility alone, per PR-24 and PR-20 before it.**

⚠ **14 clears by exactly ONE token (129 vs 128), and that is worth saying plainly.** It is
**deterministic for this bank** — the same 160 rows, the same tokenizer, so it will not drift between
runs — **but it has no headroom.** Any change to the pools, the domains, the query template or the
chat template could break it, and the failure mode is the good one: **the arm refuses before
generating, as C-18's did.** **16 is the fallback and is recorded as such.**

**The parameter is no longer hardcoded.** `--n-preamble` now overrides the preset, because **the
required length is a property of (bank, TOKENIZER) and not of the preset** — the exact confusion that
caused C-18. The default path is untouched:

* `main`, `main_longctx`, `d10` and the carrot bank still regenerate **byte-identically (3/3)**;
* `main_longpre` **with no flag reproduces `longpre10` byte-identically**;
* `--n-preamble 14` reproduces the candidate bank that was actually feasibility-tested, **verified by
  sha rather than assumed**.

**Housekeeping:** the `pre14`/`pre16` candidate banks are deleted — `pre14` was byte-identical to the
committed `longpreQ14`, and `pre16`'s measurements survive in its feasibility artifact. **The
measurements are the evidence; the rejected bank files are not** (same rule as R-51's cleanup).

**Next: re-run PR-23's arms on `longpreQ14`.** PR-23's conditions are unchanged — **a new bank does
not license new thresholds** — and its precondition (`match_ratio` 1.000 on every control row) will
be read from each run's own pre-flight, which is exactly what caught C-18.

---

### PR-24 (22:15) — **Pre-registered: re-derive the preamble length with the QWEN3 tokenizer, on feasibility alone. Same rule as PR-20, correct model this time.**

C-18 failed PR-23 because R-51's `n_preamble = 10` was chosen against **Llama's** tokenizer. This
re-derives it for Qwen3, and the instrument now reports the quantity the criterion actually depends
on:

| Qwen3, `longpre` (12) | n=1 | n=2 | n=4 | **n=8** |
|---|---|---|---|---|
| demo median / **MAX** | 13/19 | 28/36 | 56/66 | **114/128** |
| pool median / **MIN** | 133/113 | 133/113 | 133/113 | **133/113** |
| **deficit (max demo − min pool)** | 0 | 0 | 0 | **15** |

**15 tokens short, and the shortfall is on the LONGEST rows** — the mean ratio reads a comfortable
**0.925** while the min is **0.000**. **`max_n_demo`, `min_drawable_pool` and
`pool_deficit_vs_max_demo` are now emitted for exactly this reason**: PR-20 already learned once that
selecting on the mean picks a bank which silently refuses its longest rows.

**The rule, unchanged from PR-20 and applied with the right tokenizer:**

> **Choose the SMALLEST `n_preamble` whose Qwen3 `match_ratio` is 1.000 (min AND mean) at every dose.
> Selected on FEASIBILITY ALONE, never revisited against the attack rate it yields.**

**Candidates: 14 and 16.** Pool grows ~10.5 tokens/sentence (112 → 133 for 10 → 12), so 14 should
clear a 15-token deficit; 16 is the fallback. The filler pools hold **20 per split**, so neither wraps
into repetition.

**⛔ Pre-committed:**
* **R-54 removes the usual objection *in advance*, and that matters here.** On Qwen3 the preamble does
  **not** cost attack (21/160 → 23/160), so a longer preamble carries **no measured power penalty on
  this model**. That was established **before** C-18, not invented to justify lengthening.
* **This is a Qwen3 bank.** `longpre10` remains the Llama bank; **no bank is re-selected for Llama**,
  and R-50/R-52's Llama results are untouched.
* **If neither 14 nor 16 is feasible, the branch stops** — C7 on Qwen3 joins C7 on Llama as
  structurally blocked, and no third candidate is tried.
* **PR-23's conditions are unchanged.** A new bank does not license new thresholds.

---

### ⛔ C-18 (22:05) — **PR-23's GATE FAILED. The Qwen3 control arms refused before generating, because "the control is constructible on `longpre10`" was a LLAMA measurement I generalised to a method.**

**The arms did exactly what they should.** `q14_matched_d2`'s pre-flight:

```
CONTROL IS NOT COUNT-MATCHED ON SOME ROWS ... 'nondemo_matched_d2|n_examples=8':
   {'n': 40, 'min': 0.0, 'mean': 0.525, 'n_below_1': 19}
REFUSING before generating: 19 of 160 rows cannot carry this knockout
```

**The cause is mine, and it is a defaults bug in how I used my own instrument.**
`control_feasibility.py` has `--model` **defaulting to `meta-llama/Llama-3.1-8B-Instruct`**, and
**none of my argsfiles ever set it.** So R-49's "`match_ratio` 1.000 at every dose" and R-51's
selection of `n_preamble = 10` were **Llama statements**. I then wrote PR-23 asserting the control
"is fully constructible on that bank" and applied it to **Qwen3**.

**Re-measured with the Qwen3 tokenizer:**

| bank | pool (Llama) | pool (**Qwen3**) | demo @ n=8 | Qwen3 n=8 |
|---|---|---|---|---|
| `longpre10` | 138 | **112** | 114 | **INFEASIBLE** (min 0.000, mean 0.525) |
| `longpre` (12) | 160 | **133** | 114 | **INFEASIBLE** (min 0.000, mean 0.925) |

**Qwen3's tokenizer yields a smaller drawable pool for the same text**, and at `n_examples = 8` the
demo block overtakes it. **Neither existing preamble bank supports the strict control on Qwen3 at the
decisive dose.**

**PR-23 cannot be completed as specified.** Its precondition — *"`match_ratio` must be 1.000 on every
control row"* — is unmet at n=8, and PR-23 requires n=4 **and** n=8. **Gate failed; the run is
stopped, not patched into a partial claim.** The `d1`/`d2`/`d3` arms that refused produced **no
generations**, so there is nothing to salvage and nothing that could leak into a result.

#### What this is, and what it is not

**It is not a scientific negative.** Nothing was learned about demonstration-specificity; **an
instrument was mis-parameterised.** The distinction matters for what happens next: R-52's branch was
stopped because the *phenomenon* vanished, and that stayed stopped. **This one failed because I read a
Llama number and called it a property of the bank.**

**The honest repair is the same discipline as PR-20:** re-derive the preamble length **with the
Qwen3 tokenizer**, on **feasibility alone**. **And R-54 removes the usual objection** — on Qwen3 the
preamble does **not** cost attack (21/160 → 23/160), so a longer preamble carries **no measured power
penalty on that model**. That is a fact established *before* this failure, not an argument invented
after it.

**⛔ Third instance of the same class this session**, and worth naming: C-13 (a bank argument that
silently subset), C-16 (a scheduler query that silently meant nothing), and now **a `--model` default
that silently scoped a measurement to one tokenizer.** **Every one was a default or an absence
behaving as though it were a decision.**

---

### 🔴 C-17 (20:40) — **My "failed" `sbatch` calls DID create jobs. I concluded they had not, resubmitted, and ran two arms twice. No scientific harm — determinism absorbed it — but the reasoning was wrong and the check I invented was worthless.**

**What happened.** During the 19:15 SLURM outage, two `sbatch` calls returned
`Batch job submission failed: Unexpected message received`. At 19:38 I saw two PENDING jobs, checked
whether they were mine, and concluded they were the **concurrent writer's**. **They were mine:**

| job | tag | origin |
|---|---|---|
| **783468** | **`q14_demoproc`** | the "failed" submission |
| **783495** | **`q14_matched_d1`** | the "failed" submission |
| 783595 | `q14_demoproc` | my resubmission — **duplicate** |
| 783596 | `q14_matched_d1` | my resubmission — **duplicate** |

**Both of my "failed" calls succeeded.** The error was returned to me while the request was still
accepted; the jobs were stamped with the **processing** time (19:22), not my call time.

**Why my check failed, precisely.** I used two pieces of evidence and both were void:
1. *"Submit time 19:22 is after my attempts"* — **the timestamp records when the recovering control
   plane processed the request, not when it was made.** It cannot distinguish owners.
2. *"No `q14_*` run dir exists"* — **a PENDING job has no run dir.** Absence of a directory is
   absence of a *started* job, not of a job.

**I wrote at 19:38 that checking this "stops a duplicate arm from quietly doubling a control draw" —
and then the check I used let exactly that happen.**

#### What it cost, and what it did not

**No scientific harm.** The two `q14_demoproc` runs are **byte-identical**
(`gens_sha = e5d04bd9d4247819` on both, 160 rows each) — same argsfile, same seed, deterministic
decoding. The same will hold for the `matched_d1` pair, because a control draw is seeded by
`prompt_id` and the draw index.

**The cost is wasted GPU**, plus a real trap avoided by luck: **`q14_matched_d1` will exist twice, and
counting it as two of PR-23's three independent draws would be a fabricated control.** PR-23 requires
`d1`, `d2`, `d3` — **three different seeds, not three directories.**

**The correct check, used from here:** `grep -l "<tag>" outputs/boombness/logs/boomb_*.out` — **ask
what the jobs actually ran, never infer ownership from timestamps or from the absence of output.**
The redundant duplicate (783596) is **not cancelled** per the standing instruction; its result will
be **discarded, not averaged in**.

**⚠ Amended 21:10 — the "redundant" duplicate turned out to be NECESSARY.** Job 783495, the original
`q14_matched_d1`, left a run dir with **0 rows and no `DONE.json`** — it never generated. So 783596,
the duplicate I planned to discard, is now **the only route to a complete `d1`**. **The duplication
was still an error and C-17 stands; it simply happened to be load-bearing.** The rule is unchanged
and is about the counting, not the running: **`d1` contributes ONE draw to PR-23 no matter how many
directories carry its tag.**

---

### PR-23 (19:10) — **Pre-registered: C7 on QWEN3, where R-52's power blocker is measured to be ABSENT.**

R-52 closed C7 on Llama because the preamble that makes the count-matched control constructible also
removes the attack. **R-54 measured that this is a Llama property, not a property of the method.**
A per-dose power check, run **before committing any GPU**, confirms it at exactly the cells that
failed:

| bank | n=1 | n=2 | **n=4** | **n=8** | verdict |
|---|---|---|---|---|---|
| Llama longpre10 | 1/40 | 0/40 | **3/40** | **3/40** | R-52's decline |
| **Qwen3 longpre10** | 3/40 | 5/40 | **6/40** | **9/40** | **both decisive doses ≥ 4 rows** |

**Qwen3 keeps its attack on the very bank where the control is fully constructible** (`match_ratio`
1.000 at every dose, R-49/R-51, validated against a live arm). **This is not retrying a closed
branch: it is the same test in a population where the documented obstacle is measured to be gone.**

**Arms (Qwen3-14B, `longpre10`, band 7-17, 160 rows):** `q14_demoproc`, and three strict
count-matched controls `q14_matched_d1/d2/d3`. **Baseline `q13A` already exists** and will be
**re-judged in the same window** as the new arms, per R-53's design.

**⛔ Conditions are PR-19's, unchanged — no new thresholds for a new model.** CONFIRMS only if all
three hold at **`n_examples` 4 AND 8**:
1. `demoproc` removes attack: `|ΔASR| > 0.0521`.
2. Each matched control stays within **±0.0521** of baseline.
3. They separate: `|Δdemoproc − Δcontrol_mean| > 0.0417`.

**REFUTED if** the matched control removes attack comparably — **and on a properly powered population
that would be a real negative for demonstration-specificity, not a decline.** I am stating that
before the data exists: **this is the first time C7 can actually be refuted rather than declined.**

**⛔ Pre-committed:**
* **`match_ratio` must be 1.000 on every control row**, read from each run's own pre-flight.
* **Per-dose underpower rule still applies** — any dose under 4 baseline attack rows is declined even
  though the pre-check says otherwise, because the re-judge may move counts by a row or two.
* **≤2 concurrent Qwen3 loads**, per the NFS-contention lesson: two arms now, two next.
* **No cross-model magnitude comparison with Llama** — C7 is a within-bank, within-model claim.

---

### ⛔ R-54 / C-16 (19:00) — **PR-22 DOES NOT CONFIRM: C13 is LLAMA-SPECIFIC. Qwen3's attack is untouched by the preamble — which unexpectedly means C7 may be POWERED on Qwen3. And I nearly reported this from a partial judge read.**

**Artifacts:** arm `q13A` (783439); judging `xj_q_pre10` (783458), `xj_q_d10` (783459) — submitted
together, each against its own bank. **Provenance 320/320**, hash joins **320/320**.

| model | d10 | longpre10 | gap |
|---|---|---|---|
| Llama (R-53) | 27/160 = 0.1688 | **7/160 = 0.0437** | **−20 rows** |
| **Qwen3** | **21/160 = 0.1313** | **23/160 = 0.1437** | **+2 rows** |

**Gap −0.0125, inside the 0.0521 margin, and pointing the wrong way. Baseline 21 attack rows, so this
is a POWERED negative, not a decline.** Drift on identical `q4bA` completions: **0 rows.**

> **C13 is restated as LLAMA-SPECIFIC.** Ten neutral sentences that touch neither the demonstrations
> nor the query cut Llama's attack by two thirds and do **nothing** to Qwen3's.

#### 🟢 The consequence nobody was looking for: C7 may be testable on Qwen3

R-52 closed C7 because **the preamble that makes the count-matched control constructible also removes
the attack** — leaving 3 and 1 attack rows on Llama. **That trade is Llama's, not the method's.**
**Qwen3 on `longpre10` keeps 23/160 attacks**, and `match_ratio` is 1.000 at every dose on that bank
(R-49/R-51, verified against a live arm).

**So the exact obstacle R-52 declared — "the control can be built, and building it costs the
phenomenon" — does not apply to Qwen3.** That is not rescuing a failed branch by retrying it; **it is
a different population where the documented blocker is measured to be absent.** Recorded as the
evidence-backed next step, not started this tick.

#### 🔴 C-16: I read a partial judge output and it agreed with the truth

My wait loop polls `sacct`. **SLURM's control plane threw `Protocol authentication error` on both
`sacct` and `squeue`**, my loop's `grep -c` on the error output returned 0 running jobs, and it exited
**treating a query failure as job completion.** I then read **141 and 135 rows of 160** and computed a
verdict from them.

**The partial read gave the same answer as the complete one — and that is luck, not process.** It is
C-5's defect class (a partial judge dir flowing through and producing a plausible number), and this
time the plausible number happened to be right. **A process that is correct only when the truncation
is benign is not a process.**

**Fixed:** the wait now polls **the artifact** — `ALL DONE` in the judge log and the row count —
**never the scheduler.** Row counts climbing 141 → 153 → 160 is what actually revealed it.
**A completion signal must come from the thing completing, not from a service that can fail
independently.**

---

### PR-22 (18:25) — **Pre-registered: does C13 — neutral context suppressing the attack — hold on Qwen3?**

C13 (R-53) is the phase's newest claim and it is **Llama-only**: ~10 neutral sentences that touch
neither the demonstrations nor the query cut ASR from **27/160 to 7/160**. **Every other headline in
this phase that survived was tested on a second model family**, and C13 has not been.

**It is also the cheapest cross-model test available** — one arm. Qwen3's d10 baseline (`q4bA`) is
already on disk, so only the preamble-bank baseline needs generating.

**Arms:** `q13A` — Qwen3-14B, `boombness_prompt_bank_longpre10.jsonl`, 160 rows, no intervention.
Bank chosen as **R-51's feasibility-selected minimum**, not by which gave the larger Llama effect
(−21 vs −20 rows were equivalent, so nothing is being selected on).

**Judging:** `q13A` and a **re-judge of `q4bA`'s existing generations** submitted together, each
against its own bank, so the comparison is within one wall-clock window — the design R-53 established
after `compare_bank_hashes` refused a single-bank shortcut.

**CONFIRMS if** `ASR(Qwen3, d10) − ASR(Qwen3, longpre10) > MARGIN_VS_BASELINE = 0.0521`, in the same
window.
**REFUTED if** the gap falls within the margin — C13 would then be **Llama-specific**, and the claim
must be restated as such.

**⛔ Pre-committed:**
* **Qwen3's d10 baseline is 21/160 (0.1313)**, so there is real attack to lose; **if the re-judge puts
  it below 8 rows I will declare the test UNDERPOWERED and decline it**, per the rule used in PR-19.
* **Drift is measured, not assumed:** the `q4bA` re-judge doubles as a drift check against its
  original `q4bj_A` reading, exactly as R-53's did (2-4 rows on Llama).
* **This cannot rescue C7.** R-52's decline rests on within-bank counts; a cross-model result about
  C13 says nothing about demonstration-specificity.
* **No magnitude is compared to Llama's.** The two models have different baselines; the test is
  whether the *direction and margin* hold, not whether the effect is the same size.

---

### 🏆 R-53 (18:05) — **PR-21 CONFIRMS. Same judging window, each arm against its own bank: the preamble lowers ASR by ~20 rows, and measured drift is 2-4. C-15's withdrawal was right procedure; the claim now stands on evidence.**

**Artifacts:** `xj_d10` (783389), `xj_pre12` (783418), `xj_pre10` (783419) — all re-judging
**existing generations**, no new GPU.

| bank | same-window ASR | vs d10 |
|---|---|---|
| d10 | **27/160 = 0.1688** | — |
| longpre12 | **6/160 = 0.0375** | **−21 rows (−0.1313)** |
| longpre10 | **7/160 = 0.0437** | **−20 rows (−0.1250)** |

**Both gaps clear the 0.0521 margin by ~2.5×.**

#### The confound I withdrew for is now MEASURED, and it is 10× too small

Re-judging **identical completions** across sessions:

| bank | old session | PR-21 window | drift |
|---|---|---|---|
| d10 | 25 | 27 | **2 rows** |
| longpre12 | 10 | 6 | **4 rows** |
| longpre10 | 7 | 7 | **0 rows** |

**Maximum observed drift: 4 rows. The effect being explained: 20-21 rows.** The judge-session
confound was a real thing to worry about and is **an order of magnitude too small** to account for
the difference.

> **F6 is a finding, not an accounting note: ~10 neutral sentences that touch neither the
> demonstrations nor the query cut the doublespeak attack rate by roughly two thirds.** Verified at
> 17:10 that the banks differ *only* by that preamble, so the attribution is by construction.

**C-15's withdrawal was correct even though the claim survived.** When I asserted it, it rested on
three numbers from three sessions and violated PR-19's own within-bank rule. **Withdrawing an
unestablished claim and then establishing it is the right order**; the reverse would have been
publishing first and checking after.

#### 🔴 And the repo caught me mid-design

My first submission judged all three arms against **one** bank, reasoning that identical `prompt_id`s
and byte-identical `final_query_text` (4560/4560 verified) made it safe and even preferable.
**`compare_bank_hashes` REFUSED**: *"the run consumed a DIFFERENT bank than the one it is being
joined against."* **The guard does not accept reasoning, and it is right not to** — that is exactly
C-13's defect class, and this repo already had a guard for it where my own bridge script did not.
Re-run correctly with each arm against its own bank.

⚠ "Same session" here is **three jobs in one wall-clock window with the same pinned model**, not one
process. That is weaker than a single invocation and far stronger than two days apart — and **the
drift table above bounds what that weakness could cost at 4 rows.**

---

### ✏️ C-15 / PR-21 (17:40) — **I overreached: "neutral context weakens the attack" is a CROSS-BANK, CROSS-SESSION comparison that my own PR-19 forbade. Correcting it, and running the clean test.**

**The overreach.** R-52 and my summary of it presented **0.1562 → 0.0625 → 0.0437** as evidence that
the preamble weakens the attack, and I went further, calling it *"a result about the attack itself."*

**PR-19 pre-committed the opposite:** *"**Within-bank only.** `longpre` prompts are ~840 characters
longer than d10's; **its baseline ASR is its own and no magnitude is compared across banks.**"*

**And the comparison is confounded a second way.** The three baselines were judged in **three
different sessions across two days** — `p4bj_A` 2026-08-25 11:10, `p12j_A` 2026-08-26 14:08,
`p13j_A` 2026-08-26 16:13 — and this repo's **measured** cross-session judge drift is **78/96 binary
agreement**, i.e. ~19% of rows can flip. **On 25 baseline attacks that is several rows, and the
d10 → longpre12 gap is 15 rows.**

**What survives without qualification, because it never needed the cross-bank comparison:**
* **R-52's DECLINE.** `longpre10`'s decisive doses carry **3 and 1 attack rows** — that is a
  within-bank count, and PR-19's underpower rule applies to it directly.
* **R-50's within-bank C7 contrasts** on `longpre12`. Every arm there shares one bank and one
  judging session.
* **The attribution verified at 17:10** — that the banks differ *only* by the preamble. That is a
  statement about the **prompts**, not about ASR, and is unaffected.

**What is withdrawn pending test: the claim that the preamble CAUSES lower ASR.** It may well; it is
simply not established by three numbers from three sessions.

#### PR-21 — the clean test, pre-registered before it runs

**Re-judge the three baselines' EXISTING generations in ONE session**, so bank is the only thing that
varies. No new GPU: `p4bA`, `p12A` and `p13A` gens are all on disk. Prefix `xj`, pinned
`openai/gpt-4o-mini`, hash-joined.

**CONFIRMS the preamble lowers ASR if:** `ASR(d10) − ASR(longpre12) > MARGIN_VS_BASELINE = 0.0521`
**in the same session**, and the same holds for `longpre10`.
**REFUTED if** the same-session gap falls within the margin — in which case the apparent drop was
**session drift plus bank noise**, and F6's power story must be restated as "these banks happen to
have fewer attacks" rather than "the preamble removes the attack."

**⛔ Pre-committed:** this **cannot rescue C7** — R-52's decline stands on within-bank counts either
way. **It can only decide whether F6 is a finding about the attack or an accounting note about power.**
**A same-session re-judge of identical generations is exactly the measurement this repo uses to
quantify judge drift**, so it is the right instrument and not a new one.

---

### ⛔ R-52 (16:30) — **PR-20's mandated re-run is DECLINED, not refuted: both decisive doses fall below PR-19's own underpower threshold. Cutting the preamble 12 → 10 recovered nothing. The preamble path is a dead end for C7, and that is the finding.**

**Artifacts:** arms `p13*` (783039-783043), judging `p13j_*` (783116). **Provenance 800/800**, hash
joins **800/800**, `scope_live = 1.0` with no violations, and **`match_ratio` min 1.000 on all 480
control rows.** The instrument was perfect; the population was not.

| dose | baseline attacks | `demoproc` | d1 | d2 | d3 | ctrl mean |
|---|---|---|---|---|---|---|
| 1 | 2/40 | −0.0500 | −0.0500 | −0.0500 | −0.0250 | −0.0417 |
| 2 | 1/40 | +0.0000 | −0.0250 | +0.0250 | +0.0000 | +0.0000 |
| **4** | **3/40** | −0.0750 | +0.0250 | −0.0250 | +0.0750 | +0.0250 |
| **8** | **1/40** | **+0.0000** | +0.1000 | +0.1250 | +0.1250 | +0.1167 |

#### The verdict is DECLINED, and the distinction matters

PR-19: *"a dose whose baseline carries **< 4 attack rows of 40** is declared **UNDERPOWERED and
declined in both directions**."* **n=4 has 3 rows. n=8 has 1 row. Both are below the threshold, so
both are declined.**

**My readout script printed "DOES NOT CONFIRM" because I coded PR-19's three conditions without
coding its underpower rule.** That would have been a **refutation reported where the pre-registration
mandates a decline** — the difference between "the control behaved like the arm" and "there was
nothing to measure." **At n=8 `demoproc` reads +0.0000 simply because there is a single attack row in
the whole cell**, and the controls' apparent +0.1000/+0.1250 are 4-5 rows of noise on a base of one.
**Corrected before the numbers were written down.**

#### 🔴 The optimisation recovered nothing, and that is the real result

| bank | overall baseline | n=1 | n=2 | n=4 | n=8 |
|---|---|---|---|---|---|
| d10 | 25/160 = **0.1562** | 2 | 5 | **8** | **10** |
| longpre12 | 10/160 = 0.0625 | 1 | 1 | **4** | **4** |
| **longpre10** | **7/160 = 0.0437** | 2 | 1 | **3** | **1** |

**7/160 vs 10/160 is 3 rows against an 8.3-row margin — the two preamble lengths are
indistinguishable.** R-51 removed 2 sentences on a principled feasibility criterion and it **bought no
measurable power back.** If anything the count fell.

> **The preamble makes the control constructible and simultaneously removes the attack it is meant to
> test, and that trade is not tunable by preamble length.** R-50 raised this as a possibility; R-52
> establishes it by having tried the obvious remedy and measured the result.

**✅ The causal attribution is VERIFIED, not assumed (17:10).** That sentence blames the preamble, and
that is only sound if the banks are otherwise identical. Checked row by row on the 200 behavioural
core rows: **`full_prompt(longpre10) == preamble + "\n\n" + full_prompt(d10)` on 200/200**, with
`demo_block`, `final_query_text`, `demo_valence`, `n_examples`, `domain` and `family_slot` **identical
on 200/200**; `longpre12` vs `longpre10` differ **only** in preamble line count (12 vs 10) with
`demo_block` identical on 200/200. **So the ASR drop cannot be a bank-difference confound — the
preamble is the only thing that changed.** Pinned by `tests/test_preamble_is_the_only_difference.py`
(15 assertions, mutation-verified) so a future regeneration cannot quietly invalidate R-52.

**⛔ Branch stopped.** No third preamble length, no pooling of doses, no relaxed underpower rule.
**C7 remains UNRESOLVED**, now with a sharper reason than "the control cannot be built": **the control
can be built, and building it costs the phenomenon.** Any future attempt needs a way to add
non-demonstration context that does **not** dilute the attack — a different design question from the
one R-25 posed, and one this phase has no evidence bears on.

**What stands unchanged:** R-50's `n_examples=8` cell on `longpre12` (demoproc −0.1000, controls
+0.0000/+0.0500/+0.0000, separation 2.8× margin) remains the single best evidence for
demonstration-specificity ever obtained in this phase — **and it too rests on 4 attack rows, which is
why PR-19 required both doses and why C7 is still unresolved.**

---

### 🔎 DR-8 (15:15, DEEP REVIEW) — **1406/1 → 1407/0. My own argsfile guard cried wolf during a live sweep, which is a defect in the guard. Fixed, and the repo hygiene that feeds the C-2 check is repaired.**

**Suite:** `1406 passed, 1 failed` → **`1407 passed, 0 failed`** after the fix below.

#### 🔴 The guard failed on nothing, which is worse than not failing

`test_argsfiles_match_runs` (R-43) reported a mismatch during the full-suite run — and **passed on its
own minutes later.** The cause: **a run directory appears the moment a job starts, but `RUNMETA.json`
is written at the end.** The `p13` arms (PR-20's mandated re-run) were mid-generation, so the guard
compared against runs that had not recorded their `argv` yet and called it a mismatch.

**That is a false alarm precisely when the suite is most likely to be run — during a sweep.** A guard
that cries wolf whenever arms are in flight is a guard that gets ignored, which is the failure mode
that makes guards worthless. **Fixed: run dirs without a `DONE.json` are SKIPPED, not failed** —
in-flight is "not comparable yet", not "wrong".

**Mutation-verified that it did not become toothless:** on a *completed* run the real args still
match and a mutated `--max-new 999` still fires; **3 in-flight dirs are currently skipped.**

#### Repo hygiene, because it feeds a real check

* **35 MB of rejected candidate banks removed** (`pre6`, `pre8`, `pre10`). Verified safe first:
  **0 of them were tracked**, `pre10` is **byte-identical** to the committed `longpre10`
  (`87343411e3d60ed6`), and **R-51's evidence survives independently** in the
  `control_feasibility` artifacts (pool 96 / 118 / 138, `n=8` min 0.000 / 0.000 / 1.000).
  **The measurements are the evidence; the rejected bank files are not.**
* **`tmp*/` added to `.gitignore`.** PyTorch writes an RPC scratch dir into the repo root on every
  test run that imports torch. It carries no research content, **but an untracked directory dirties
  `git status`, which this project reads every tick to detect artifact corruption (C-2).**
  Verified: a torch-importing test now leaves the tree clean, and `git check-ignore` confirms the
  rule. **A check that is routinely noisy is a check that gets ignored** — the same principle as the
  guard fix above, arriving twice in one review.

**Kept banks:** `d10`, `longpre` (12), `longpre10` (10, the PR-20 winner). Byte-identity tests still
**3/3**; `check_all` 6/6.

---

### 🔧 R-51 (15:05) — **PR-20 resolved on feasibility alone: `n_preamble = 10` is the principled minimum. The re-run it mandates is submitted, and I am honouring that commitment even though the expected gain is small.**

| `n_preamble` | pool | n=1 | n=2 | n=4 | **n=8** | feasible everywhere? |
|---|---|---|---|---|---|---|
| 6 | 96 | 1.000 | 1.000 | 1.000 | **min 0.000** (mean 0.175) | ❌ |
| 8 | 118 | 1.000 | 1.000 | 1.000 | **min 0.000** (mean 0.650) | ❌ |
| **10** | **138** | 1.000 | 1.000 | 1.000 | **1.000** | ✅ **selected** |
| 12 (incumbent) | 160 | 1.000 | 1.000 | 1.000 | 1.000 | ✅ but 22 tokens of surplus |

**`n_preamble = 8` is the instructive failure.** Its pool of **118 exceeds the median demo block of
114** — and it still fails, because at `n_examples = 8` the demo block reaches **128 tokens on the
longest rows.** Its **mean** ratio reads a respectable **0.650** while its **min** is **0.000**.
**Selecting on the mean would have picked a bank that silently refuses its longest rows**, which is
R-24/R-26's under-matching lesson arriving through a new door. **The criterion is the min, and this is
why.**

**Selected on feasibility alone, per PR-20, and never revisited against the attack rate it yields** —
that would be selecting on the outcome, which is what D-10 forbids for the domains. The value is now
in the preset with the measurements written beside it.

**Verified:** the preset-built bank is **byte-identical** to the standalone candidate
(`87343411e3d60ed6`), `--strict` gives 560 families / **0 violations**, and `main` + `main_longctx`
still regenerate **byte-identically (3/3)**.

#### ⛔ Honouring a pre-registration that is now inconvenient

PR-20 committed: *"If the winner is smaller than 12, C7's PR-19 test must be RE-RUN on it from
scratch."* **The winner is smaller. So the re-run is submitted** — five arms on `longpre10`.

**I want to be explicit that I expect little from it.** The change is **2 sentences of ~110
characters**, and `longpre10` prompts are still **~2.2× d10's length**, so most of the dilution that
halved the attack remains. **PR-20 also pre-committed that a smaller preamble is not expected to
rescue PR-19 and cannot undo its failure at n=4.**

**I am running it anyway because the commitment was made before the winner was known**, and honouring
pre-registrations only when they are cheap is not honouring them. **If the test is still underpowered,
that is the answer** — PR-20 pre-committed that too.

---

### PR-20 (15:20) — **Pre-registered: pick the MINIMUM sufficient preamble, on feasibility alone, before any ASR is measured.**

R-50 found that the preamble which made the control constructible **halved the attack**
(baseline ASR 0.1562 → 0.0625), leaving 4 attack rows per dose and an underpowered test.

**Part of that is my own arbitrary choice.** R-48 measured the requirement as **≥116 non-demo tokens
at `n_examples`=8**; I set `n_preamble = 12`, which delivered a pool of **160** — about **44 tokens
more than needed**. **Every one of those surplus tokens dilutes the attack for no methodological
gain.**

**The rule, fixed before any bank is built or any ASR is seen:**

> **Choose the SMALLEST `n_preamble` whose `match_ratio` is 1.000 (min AND mean) at every dose.
> The choice is made on FEASIBILITY ALONE and is NEVER revisited in light of the attack rate it
> yields.**

**This is D-10's discipline applied to a continuous parameter** — the same reason the ten domains
were accepted on their audit and never on their effect size. **Selecting a preamble length by which
one preserves the most attack would be selecting on the outcome**, and would invalidate C7 on the
resulting bank just as surely as a relaxed margin would.

**Method (CPU only, ~1 minute per candidate):** build banks at `n_preamble ∈ {6, 8, 10}` and run
`control_feasibility.py` on each. The incumbent is 12. **The winner is the smallest candidate that is
feasible at all four doses; if none of 6/8/10 is feasible, 12 stands** and R-50's power limit is
intrinsic rather than self-inflicted.

**⛔ Pre-committed:**
* **No ASR is computed on any candidate bank before the choice is made.** The selection uses
  `match_ratio` only.
* **If the winner is smaller than 12, C7's PR-19 test must be RE-RUN on it from scratch** — the R-50
  numbers belong to the 12-sentence bank and are not transferable.
* **A smaller preamble is not expected to rescue PR-19.** It may recover some power; **it cannot
  change the fact that PR-19 already failed at n=4 on a bank where the control was valid.** That
  result stands regardless.
* **This is not a search for a bank that confirms C7.** If the minimum-sufficient bank still gives an
  underpowered test, that is the answer and it will be reported as one.

---

### ⚖️ R-50 (14:55) — **PR-19 DOES NOT CONFIRM. It required both doses; `n_examples=8` holds all three conditions cleanly and `n_examples=4` fails. And the bank that made the test possible also halved the attack it was meant to test.**

**Artifacts:** arms `p12*` (782836-782840), judging `p12j_*` (782891).
**Provenance 800/800**; hash joins **800/800**. **Preconditions met:** `scope_live = 1.0`, no
violations, and **`control_draw_match_ratio` min = 1.000 on all 480 control rows** — the count-matched
control that has been impossible for the whole phase was real on every row.

| dose | baseline attacks | `demoproc` ΔASR | ctrl d1 | ctrl d2 | ctrl d3 | ctrl mean |
|---|---|---|---|---|---|---|
| 1 | 1/40 | −0.0250 | −0.0250 | +0.0000 | −0.0250 | −0.0167 |
| 2 | 1/40 | −0.0250 | −0.0250 | +0.0250 | +0.0250 | +0.0083 |
| **4** | **4/40** | **−0.1000** | **−0.1000** | −0.0750 | −0.0500 | −0.0750 |
| **8** | **4/40** | **−0.1000** | +0.0000 | +0.0500 | +0.0000 | **+0.0167** |

**`n_examples = 8` — all three conditions HOLD.** `demoproc` −0.1000 clears the 0.0521 margin; all
three controls sit within it (+0.0000 / +0.0500 / +0.0000); separation **0.1167**, **2.8× the
arm-vs-arm margin**. **A count-matched mask of the same size elsewhere did not remove the attack, and
the demonstration mask did.**

**`n_examples = 4` — FAILS.** Control draw d1 removed **exactly as much as `demoproc`** (−0.1000
each). Conditions 2 and 3 both fail.

#### ⛔ The verdict is the pre-registered one

PR-19 states: *"CONFIRMS only if ALL THREE hold, at `n_examples` 4 **AND** 8."* **One dose of two is
not that. PR-19 does not confirm, and C7 stays UNRESOLVED.** Reporting the n=8 cell alone as C7
confirmed would be choosing the dose that worked after seeing both — the thing the pre-registration
exists to stop.

#### 🔴 Why this is thin, and the bank's own cost

**Both decisive cells rest on 4 baseline attack rows of 40.** PR-19's underpower rule was "< 4 rows",
so 4 does **not** trigger it — **it sits exactly on the boundary.** `demoproc`'s −0.1000 is 4 rows
against a 2.1-row margin: **1.9×**, as thin as C12.

**And the preamble that made the control constructible also weakened the attack it was testing:**

| bank | overall baseline ASR | n1 | n2 | n4 | n8 |
|---|---|---|---|---|---|
| d10 | 25/160 = **0.1562** | 2/40 | 5/40 | 8/40 | **10/40** |
| **longpre** | 10/160 = **0.0625** | 1/40 | 1/40 | **4/40** | **4/40** |

**The attack rate more than halved.** That is not a confound in the comparison — every PR-19 contrast
is within-bank, as pre-committed — **but it is the reason the test is underpowered, and it is a
property of the fix itself.** ~840 characters of neutral context between the reader and the
demonstrations dilutes the attack. **Making the control constructible and keeping the attack strong
may be in tension**, and that possibility was not visible before this run.

**Not rescued.** No fourth draw, no dose pooling, no relaxed margin. **The honest next step is more
rows at n=8 on this bank** — the only cell that behaved — to see whether it survives real power. That
is a decision about spending GPU on a thin cell, and I am not taking it unilaterally.

---

### PR-19 (13:40) — **Pre-registered: C7 at last. Is the demonstration knockout DEMONSTRATION-SPECIFIC at the doses where the effect lives?**

**This is the question the whole phase has been unable to ask.** R-24/R-25 established that a
count-matched non-demonstration control **cannot be built** at `n_examples` 4 or 8 on any prior bank;
R-26 got one suggestive cell at n=2 by accident of the capped policy; R-46 built the wrong fix; R-48
specified the right one; R-49 delivered a bank where **`match_ratio` is 1.000 (min and mean) at every
dose.** Now the control exists and the claim can be tested properly.

**The claim.** *Masking the demonstration positions removes the attack because they are the
DEMONSTRATIONS, not because masking that many positions anywhere would do it.*

**Arms (Llama, `boombness_prompt_bank_longpre.jsonl`, band 6-14, 160 rows each):**
`p12A` (clean), `p12_demoproc` (`demo_processing_only`), and **three independent strict
count-matched controls** `p12_matched_d1/d2/d3` (`nondemo_matched_d*`) — three, because a single
draw that happens to hit nothing is a lucky draw rather than a control.

**⛔ CONFIRMS only if ALL THREE hold, at `n_examples` 4 AND 8 (the doses that were untestable):**
1. **`demoproc` removes attack:** `|ΔASR| > MARGIN_VS_BASELINE = 0.0521`.
2. **The matched control does NOT:** each draw within **±0.0521** of baseline.
3. **They separate:** `|Δdemoproc − Δcontrol_mean| > MARGIN_ARM_VS_ARM = 0.0417`.

**REFUTED if** the matched control removes attack comparably — that would mean the effect is about
**masking N positions**, not about the demonstrations, and **every "demonstration retrieval" framing
in this phase would need renaming.** I am stating that consequence now, before the data exists.

**⛔ Pre-committed limits.**
* **Within-bank only.** `longpre` prompts are ~840 characters longer than d10's; **its baseline ASR
  is its own** and no magnitude is compared across banks. C7 is a statement about this population.
* **Per-dose underpower rule:** a dose whose baseline carries **< 4 attack rows of 40** is declared
  **UNDERPOWERED and declined in both directions** — the rule that made me decline R-23's n=1 cell.
* **`match_ratio` must be 1.000 on every row of every control arm**, verified from the run's own
  pre-flight, not assumed from R-49. An under-matched control that shows no effect is an artifact of
  the under-matching (R-24, R-26).
* **`rescue_liveness` is irrelevant here; `knockout_liveness` is not** — `frac_rows_scope_live` must
  be 1.0 with no violations on all four intervention arms or that arm is **UNMEASURED, not null**.
* **n=1 and n=2 are reported but are NOT the claim** — they were already testable and R-26 already
  spoke to n=2.

**Judging:** pinned `openai/gpt-4o-mini`, prefix `p12j`, hash-joined as always. **No number is read
until all five arms land and the match ratios are checked.**

---

### 🏆 R-49 (13:20) — **THE BANK IS FIXED. A neutral preamble emitted OUTSIDE `demo_block` makes the count-matched control feasible at EVERY dose — 1.000 min and mean. C7, the phase's only unresolved claim, is unblocked.**

R-48 specified the requirement (**≥76 more non-demo, non-query tokens at `n_examples`=8, emitted
outside `demo_block`**). This implements it. `main_longpre` (12 filler sentences) writes them into
`full_prompt` but **not** into `body` — the opposite of R-46's `main_longctx`, which appended to
`body` and grew the demonstration block instead.

| bank | pool | n=1 | n=2 | n=4 | n=8 |
|---|---|---|---|---|---|
| d10 | 30 | 1.000 | 0.875 | **0.000** | **0.000** |
| longctx (R-46) | 30 | **0.000** | 0.000 | 0.000 | 0.000 |
| **longpre** | **160** | **1.000** | **1.000** | **1.000** | **1.000** |

**`min` and `mean` are both 1.000 at every dose** — not a mean that hides refused rows. **The strict
count-matched control can now be built on every row of the population.**

#### Verified structurally, not just by the ratio

| check | result |
|---|---|
| `demo_block` unchanged | **78 → 78** (n=1), **638 → 638** (n=8) — the preamble is provably outside it |
| drawable outside | 90 → **840** chars |
| preamble contains codeword / concept | **False / False** — it cannot perturb the target counts |
| 2×2 preamble invariant | **640 core families checked, 0 with a non-identical preamble** |
| `--strict` | 560 families, **0 violations** |
| tokenization audit | `rows ok=4560 bad=0`, **0 alignment violations** |
| `main` + `main_longctx` regression | **3/3 byte-identical** |

#### 🔴 The regression that fired, and why it mattered

My first version added `preamble` and `n_preamble_lines` to **every** row. That changed the JSON of
every bank — **including `main`'s — and broke byte-identity immediately.**
`test_bank_regenerates_byte_identically` caught it **before anything was committed**, which is
precisely the guard R-42/R-43 built for. **A bank that silently grows a key is a bank whose sha no
longer matches the artifacts joined to it.** The fields are now emitted **only when a preamble
exists**, and the reason is written at the call site rather than left to be rediscovered.

**Nothing else is touched:** `main` and `main_longctx` regenerate byte-identically, and 3 lines were
replaced (the signature, the `full` assembly, and the block-key passthrough) with the new fields
conditional.

**Next: pre-register the C7 experiment on this bank before any arm is submitted.** The claim under
test is demonstration-specificity **at `n_examples` 4 and 8** — the doses R-25 declared untestable and
that have been untestable for the whole phase.

---

### 📐 R-48 (12:45) — **R-25's limitation is now a NUMBER: the bank needs ≥76 more non-demo tokens at `n_examples=8`, and no existing mechanism can supply them. Every lever was measured, not argued.**

With a validated 49-second instrument (R-47), "it needs a bank redesign" can be replaced by a
specification. **Three questions, all answered empirically:**

**1. What is actually outside `demo_block`?** Read off a row directly: **nothing precedes it**
(`demo_block` starts at character 0), and the 90 characters after it are **the query** — the span a
control must never touch. **So the entire drawable pool of ~30 tokens is chat template.** The bank
has, effectively, no neutral context at all.

**2. Does the filler lever work?** No — **it lands inside `demo_block`** (R-46), which is why the
long-context bank is infeasible at *every* dose including the one that previously worked.

**3. Does the role-style lever work?** `wrap_role` genuinely emits text **outside** `demo_block`, so
this was the one remaining cheap path. **Measured on the bank's own `role_style` block, 100 rows per
dose:**

| dose | demo tokens | pool, `plain` | pool, role wrapper | feasible? |
|---|---|---|---|---|
| 2 | ~26 | 30 → mean **0.875** | **40** → **1.000, feasible** | ✅ improved |
| 4 | ~56 | 30 → 0.000 | **40** → 0.030 | ❌ |
| 8 | ~116 | 30 → 0.000 | **40** → **0.000** | ❌ |

**The wrappers buy exactly 10 tokens.** That is enough to lift `n_examples=2` from 0.875 to a clean
1.000 — a real gain — and **nowhere near enough for the doses where the effect lives.**

#### The specification

> **To test demonstration-specificity at `n_examples = 8`, the bank must carry ≥ 116 non-demo,
> non-query tokens. It carries 40 at best. The deficit is ≥ 76 tokens**, and it must be emitted
> **outside `demo_block`** — which is a change to `build_prompt`'s output contract and to what every
> committed bank and every knockout arm treats as the demo span.

**Every cheaper option is now excluded by measurement rather than by argument:** filler (inside the
block), role wrappers (+10 tokens), and shorter demos (would change the dose, which *is* the
variable). **This is the whole answer to "what would it take", and it cost about three minutes of
CPU.**

⚠ **One genuine, small win worth keeping:** at `n_examples = 2` a role-style wrapper makes the strict
control **fully feasible (1.000 vs 0.875)**. **But C7's cell is `plain`**, and swapping role style to
buy feasibility would confound the arm with a design factor the bank varies deliberately — **so it is
recorded as available, not used.**

---

### ✅ R-47 (12:15) — **The quarantined instrument is fixed and now reproduces the real pre-flight EXACTLY. The cause was not what I guessed — it was `len()` on a returned tuple.**

R-46 quarantined `control_feasibility.py` for disagreeing with reality and offered a **guessed**
cause: a templating mismatch. **That guess was wrong, and the guess is corrected here rather than
left standing.**

**First, what was NOT wrong.** The script's demonstration-position counts matched the real arms
**row for row** — median **13 / 28 / 56 / 114** across `n_examples` 1/2/4/8, identical to the
`rescue_liveness.n_positions_written` recorded by `p7_rescue_L14`. **Templating, `resolve_occurrences`
and `demo_key_positions` were all correct all along**, which is exactly why the wrong numbers looked
plausible.

**The actual defect:** `nondemo_control_draw` returns a **tuple `(positions, record)`**, and the
script did `len(drawn) / len(dk)`. **`len()` of that tuple is 2.** Every ratio was `2 / n_demo_keys`:
**2/18 = 0.111** and **2/13 = 0.154** — precisely the `min=0.111, mean=0.158` it reported.

**The fix reads `match_ratio` and `n_pool` from the record the function itself computes**, rather than
re-deriving them beside it. **A derived quantity should come from the thing that derived it.**

#### Validation against ground truth

| bank / dose | real pre-flight (R-24/R-25, job 780231 + 780297) | fixed script |
|---|---|---|
| d10, n=1 | min 1.0, mean 1.0, 40/40 feasible | **1.000 / 1.000, feasible=True** |
| d10, n=2 | 35/40 feasible, **mean 0.875** | **min 0.000, mean 0.875** |
| d10, n=4 | 0.0 / 0.0 | **0.000 / 0.000** |
| d10, n=8 | 0.0 / 0.0 | **0.000 / 0.000** |

**Exact agreement, including the 0.875 mean at n=2** — a number nothing in the script could have
produced by coincidence. **Quarantine lifted.**

#### R-46 independently confirmed, now by a trustworthy instrument

| bank | n=1 | n=2 | n=4 | n=8 |
|---|---|---|---|---|
| d10 | demo 13, pool 30 → **1.000** | 28 / 30 → 0.875 | 56 / 30 → **0.000** | 114 / 30 → **0.000** |
| **longctx** | demo **188**, pool **30** → **0.000** | 200 / 30 → 0.000 | 228 / 30 → 0.000 | **285** / 30 → **0.000** |

**The long-context bank is infeasible at EVERY dose, including `n_examples = 1` where d10 was fine.**
It did not merely fail to help — **it destroyed the one dose that previously worked**, exactly as
R-46's character counts predicted. **The pool is 30 on both banks; only the demo block moved.**

#### Two source-scanning guards had to be narrowed, and the product was checked FIRST

Adding the `main_longctx` preset broke `test_slot_disjointness.py`, and the new
`test_control_feasibility.py` failed on its own docstring. **Neither was a product defect, and both
were confirmed so before either test was touched:**

* `core2x2_slot3` still carries `slots=[3]`, and **both banks contain 640 slot-3 rows.** The guard
  did `src.index("core2x2_slot3")` and my preset **mentions that name earlier in the file** when
  overriding its filler, so it inspected the wrong 400 characters. **Re-anchored on
  `dict(name="core2x2_slot3"` — the definition, not a mention.**
* The feasibility test forbade the string `len(drawn)` anywhere, but the module docstring **quotes
  the defect on purpose.** **Scoped to code, past the docstring** — a guard that cannot tell an
  explanation from the thing it explains would forbid documenting the bug.

**Both re-verified by mutation:** `slots=[2]` still fires the first; a reintroduced `len(drawn)`
still fires the second. **The tests were narrowed, not weakened, and in both cases I checked the
product was right before deciding the test was wrong.** Full suite: **1407 passed, 0 failed.**

**Value of the CPU path:** this answer took **49 seconds** on `cpu-killable`. The GPU smoke submitted
to obtain the same number (**782572**) sat PENDING for **three hours** and then **FAILED** — it would
have been the fourth arm to refuse before generating. **A number that needs no model should never
wait on a GPU queue.**

---

### ⛔ R-46 (12:00) — **THE LONG-CONTEXT BANK FAILS ITS OWN GATE, and it fails in the opposite direction: `filler_near` grows the DEMONSTRATION BLOCK, not the drawable pool. Branch stopped. Also: my feasibility script disagrees with ground truth and is NOT to be trusted yet.**

#### The finding, read straight off the bank files

`demo_block` is the span the knockout masks **and** the span a count-matched control must match. The
control draws from **outside** it, minus the protected query span. Median characters:

| n_examples | d10 `demo_block` | d10 **outside** | longctx `demo_block` | longctx **outside** |
|---|---|---|---|---|
| 1 | 78 | **90** | **1080** | **90** |
| 2 | 154 | **90** | 1159 | **90** |
| 4 | 318 | **90** | 1328 | **90** |
| 8 | 638 | **90** | **1644** | **90** |

**The outside is 90 characters on both banks, at every dose. It did not move.** What moved is the
demonstration block, from 638 to **1644** characters at `n_examples = 8`.

**Cause, confirmed by inspection:** with `example_position = "near"`, `build_prompt` places filler
**in front of the demo sentences inside the same context block**, and `demo_block` is recorded as that
**whole block** — the longctx row's `demo_block` is 17 lines: **16 filler + 1 demonstration.** So
turning filler on adds text to the exact span the control is trying to match against.

> **The redesign makes the problem strictly worse.** It was supposed to grow the drawable pool; it
> grew the thing the pool has to match. `match_ratio` cannot improve and can only fall.

**⛔ Branch stopped, not rescued.** More filler, a different `example_position`, or a bigger
`n_filler` all move the same text into the same block. **R-25's requirement stands unmet**, and the
requirement is now sharper than R-25 could state it:

> **The added context must be emitted OUTSIDE `demo_block`** — a separate preamble field the generator
> records as not-demonstration. That is a change to `build_prompt`'s output contract and to what every
> downstream consumer treats as the demo span, **not a preset.** It is a real piece of work and it is
> **not** started without a decision, because it changes a field that every committed bank and every
> knockout arm in this repo joins on.

**Artifacts kept, not deleted:** `boombness_prompt_bank_longctx.jsonl` and the `main_longctx` preset
remain committed and pass `--strict` (560 families, 0 violations) and the tokenization audit
(`rows ok=4560 bad=0`, 0 alignment violations, job 782571). **They are a valid bank that is simply
useless for this purpose**, and the preset is the record of an approach that was tried and why it
cannot work.

#### 🔴 And a defect in my own instrument, before anyone quotes its numbers

`src/boombness/control_feasibility.py` (new, CPU-only) was written to read `match_ratio` without a
GPU — job 782572 had been PENDING for **three hours** for a number that needs no model. **It
disagrees with measured reality and must not be used:**

| bank / dose | real pre-flight (R-24, job 780231) | my script |
|---|---|---|
| d10, `n_examples`=1 | **1.0** (40/40 rows feasible) | **0.111 min / 0.158 mean, feasible=False** |

**Its own docstring says "a feasibility check that disagrees with the thing it predicts is worse than
no check", and it does.** ⚠ **The cause guessed here — a templating mismatch — was WRONG; see R-47.**
The real defect was `len()` on a returned `(positions, record)` tuple. **The refusal to report its
ratios until validated was correct; the diagnosis offered alongside it was not.**

**✅ Closed 15:40:** the instrument is now validated **twice** — against R-24's historical d10
pre-flight (1.0 / 0.875 / 0.0 / 0.0, reproduced exactly) **and against a LIVE arm on a bank it was
not tuned against**: `p13_matched_d1` on `longpre10`, where the CPU prediction of **min 1.000 at all
four doses** matches the arm's own recorded pre-flight **exactly, 40 rows per dose.** R-47's
outstanding `--verify-against` caveat is discharged by a real run rather than a flag.

**The R-46 conclusion above does NOT depend on that script.** It rests on `demo_block` character
counts read directly from the two bank files, and on the 17-line `demo_block` containing 16 filler
sentences. **The bad instrument is reported as a defect; the finding stands without it.**

---

### 🔧 R-45 (08:50) — **R-25's bank-design fix, built. It needed NO new machinery — the mechanism already existed and was simply switched off. Two gates pass; the decisive feasibility check is queued.**

**Decision:** the user chose the **longer-context bank** (over the benign-register concept, or both).
That unblocks **C7 — the phase's only UNRESOLVED claim.**

#### The fix is a preset, not a rewrite

R-25 concluded the control needs *"a bank whose non-demonstration context is long enough to match a
106-token demo block without touching the query."* **`build_prompt` has emitted exactly that since
before this phase**: `n_filler` neutral sentences drawn from `pools[domain|filler]`, which are
**non-demo, non-query positions — precisely the pool `nondemo_control_draw` draws from.** They were
simply **empty**, because `filler_near` defaults to `False` and the behavioural blocks sit at
`example_position="near"`.

**So the "bank-design change" is one preset that turns them on for the two behavioural blocks.**

**`main` is deliberately untouched** — every committed bank was built with the current defaults and
`bank_rows_sha16` is joined on. **Verified, not asserted:** `test_bank_regenerates_byte_identically`
still passes 3/3, so the carrot and d10 banks regenerate **byte-identically**. **0 lines deleted.**

**Sizing, and why 16:** filler sentences are ~12-14 tokens, so 16 gives **~200 drawable tokens**
against a 106-token demo block at `n_examples=8`; the filler pools hold **20 per split**, so `_take`
never wraps into repetition. Filler is selected by `family_slot`, **shared across the 2×2**, so all
four cells receive the same filler and the exact-word-swap invariant is untouched — **`--strict` is
the check on that, not this reasoning.**

#### Gates so far

| gate | result |
|---|---|
| `prompt_families --strict` | `families checked=560 violations=0`, `duplicates dropped=0` |
| `tokenization_audit` (job 782571) | `rows ok=4560 bad=0`, **`token-alignment violations=0`** |
| `main` preset regression | **3/3 byte-identical** |
| shape | 4560 rows, same as d10; median prompt at `n_examples=8` **726 → 1726 chars** |

#### ⛔ The check that decides whether this worked at all

**Job 782572** (PENDING under fair-share): a 16-row smoke with `nondemo_matched_d1`, whose **only**
purpose is the pre-flight `control_draw_match_ratio` per dose. **On the d10 bank that ratio was
1.0 / 1.0 / 0.0 / 0.0 across `n_examples` 1/2/4/8, and the arm refused before generating (R-24, R-25).**

**If it is not ~1.0 at n=4 and n=8 on this bank, the redesign did not work and I will say so** — more
filler would then be a search for a number rather than a fix, and R-25's branch stays closed.
**Nothing behavioural is submitted until that ratio is read.**

---

### 🔎 DR-7 (08:10, 4h DEEP REVIEW) — **Suite 1402/0, and the first EXHAUSTIVE liveness sweep of the phase: all 31 knockout arms pass their own declared contract. One edit count independently corroborates R-33.**

**Suite:** `1402 passed, 7 skipped, 0 failed`, serial and exclusive; working tree clean.

**Liveness had only ever been checked arm-by-arm as arms landed.** This is the first sweep over
**every knockout arm the phase produced** — 31 of them, spanning both models, three banks, controls,
rescues and smokes — each checked against the contract `pair_common` declares **for its own scope**
(`LIVENESS_REQUIREMENT` / `LIVENESS_MUST_BE_ZERO`), not against a rule restated in the audit.

| check | result |
|---|---|
| arms swept | **31** |
| `frac_rows_scope_live` = 1.0 | **31/31** |
| `scope_violations` non-empty | **0** |
| arms failing their **own** declared contract | **0** |
| `total_decode_edits` = 0 where the scope requires it | **all prefill-only scopes** |

**Nothing in this phase is a null-without-firing.** Every scope that had to edit did; every scope that
had to leave a half alone did.

#### The number that corroborates R-33 without being designed to

The two smokes differ by **exactly 2×**:

| smoke | prefill edits |
|---|---|
| `p7smoke_rescue_L14` (clean donor) | **146,322** |
| `p7smoke_identity_L14` (`--rescue-donor self`) | **292,644** |

**292,644 / 146,322 = 2.000 exactly.** Under `--rescue-donor self` the donor-capture forward runs
**under the arm's own hooks**, so the knockout fires **once more** than in the clean-donor case.
**That is the mechanical signature of the identity control actually capturing under the arm** — which
is precisely the property that makes R-33's 8/8 byte-identical result meaningful. **It was never
designed as a check and I did not look for it; it falls out of a sweep that had a different purpose.**

**Cross-arm consistency also holds where it must:** `p7_rescue_L14`, `p7_rescue_L5` and
`p4b_demo_processing_only` all report **3,017,169** prefill edits — same knockout, same rows, the
rescue patch being a separate hook — and the `q6b` trio all report **3,848,944**. **A rescue arm whose
knockout edit count drifted from its own knockout-only arm would mean the two were not comparable**,
and none did.

---

### ✅ R-44 (07:42) — **Systematic sweep: ALL EIGHT distinct published percentages are row-exact. C-14 was the only instance of the class, and the class is now guarded by a test.**

C-14 showed the round-then-divide defect is **live** — three occurrences now (DR-4; C-14; and DR-4's
original) — and that I caught two of them **by accident**. So rather than assume the rest are fine,
every distinct percentage in both deliverables was **recomputed from row counts**:

| published | claim | row-exact | rows |
|---|---|---|---|
| 69.2% | C9 Llama/A refusal removed | **69.23%** | 18/26 |
| 81.0% | C9 Qwen3/A | **80.95%** | 17/21 |
| 92.3% | C9 Qwen3/B | **92.31%** | 12/13 |
| 58.1% | C9 Llama/B | **58.06%** | 18/31 |
| 96.2% | C11 query-span refusal removed | **96.15%** | 25/26 |
| 16.7% | C9 Llama/A ASR recovery | **16.67%** | 4/24 |
| 37.5% | C11 query-span ASR recovery | **37.50%** | 9/24 |
| 36.4% | C12 demo-24 vs full demo patch | **36.36%** | 4/11 |

**8 / 8 correct.** **C-14's 16.6% was the only bad figure the class ever produced here, and it was
mine, introduced during the fix and withdrawn on the next pass.**

**Made permanent: `tests/test_published_percentages_are_row_exact.py`.** It recomputes each figure
from the judge rows and asserts the deliverable still agrees — so a figure edited to a wrong value,
**or an artifact regenerated differently**, fires. Three design points:
* it **skips** when `outputs/` is absent, guarding a working tree rather than a checkout;
* it asserts the guard covers **≥ 7 cells**, because a vacuous guard passes forever (the R-21 /
  `coherence_gate` lesson, met for the third time this sprint);
* it has a dedicated test that **`16.6%` may appear only inside the C-14 correction that explains
  it** — a withdrawn figure creeping back as a live number is exactly how retractions get undone.

**Mutation-verified:** 69.23% passes against a published 69.2 and fails against a fabricated 71.0.

> **The audit arc is closed.** Across C-13, R-41, R-42, R-43, C-14 and R-44 it produced: one silent
> subsetting defect, two claims with no reproduction command at all, one backwards correction, and
> four permanent guards. **Every one of those existed before the audit began and none would have
> been found by reading.**

---

### ✏️ C-14 (07:12) — **I corrected a figure BACKWARDS. The Llama ASR recovery is 16.7%, not 16.6% — my "fix" was itself the round-then-divide artifact, committed in the same breath as the rule against it.**

**What happened.** In `cca3e996` I recorded that the sprint summary "quoted **16.7%** for the Llama ASR
recovery; exact is **16.6%** — the same round-then-divide slip as DR-4", and changed it. **That is
inverted.** Recomputed from rows on the final consistency pass:

| method | value |
|---|---|
| **rows (honest)**: `(5 − 1) / (25 − 1)` attack rows | **16.67% → 16.7%** |
| rates: `(0.0312 − 0.0063) / (0.1562 − 0.0063)` | 16.61% → 16.6% |

**The published ASR rates are themselves rounded** — 5/160, 1/160 and 25/160 are 0.03125, 0.00625 and
0.15625, shown to four places. **Dividing those rounded rates is exactly the artifact DR-4 identified,
and it is what produced my "exact" 16.6%.** The original 16.7% was right.

**So I applied the round-then-divide error while writing the rule against it**, and labelled the
result a correction. **The correction is WITHDRAWN. 16.7% stands**, restored in the handoff (3
occurrences) and in the summary, whose corrections table now carries C-14 instead of the bogus row.

**Nothing else moves** — 16.7% vs 16.6% changes no verdict; the ASR rescue was Outcome C either way,
and the recovery figure was never a registered quantity.

**Why it is logged at all:** DR-4 and DR-5 both concluded *"row counts are the honest denominator"*,
and I then failed to apply it to the one number I was actively editing. **The lesson is that a rule
stated is not a rule applied**, and the only reason this surfaced is that the final pass recomputed
the figure from rows instead of trusting the correction that had just been committed.

---

### ✅ R-43 (06:40) — **The manifest's GPU rows verified end-to-end: all 38 committed argsfiles still match the `argv` their runs actually executed. 0 differences, 0 orphans — and it is now a test.**

The manifest points at `runargs/*/*.txt` for every GPU arm, and **those files are the only record of
how an arm was invoked.** Nothing stopped one from being edited after its job was submitted — at which
point the manifest would name a command **that never ran**, silently and permanently. Since
`RUNMETA.json` records each run's real `argv`, the two can be compared.

| check | result |
|---|---|
| argsfiles with a matching run on disk | **38** |
| **argsfiles whose committed args differ from the run** | **0** |
| argsfiles with no corresponding run (orphans) | **0** |

**So every committed argsfile is the one that produced its artifact** — the GPU rows of the manifest
are now verified in the only sense available without re-burning the GPU time.

**Made permanent as `tests/test_argsfiles_match_runs.py`**, with two properties worth noting:
* it **skips cleanly** when `outputs/` is absent (that directory is gitignored, so a fresh clone has
  no run dirs) — this guards a *working tree*, not a checkout;
* it asserts **`len(pairs) >= 20`**, because a guard that silently matches nothing passes forever.
  **A vacuous check is worse than no check**, and this sprint has already met that failure twice
  (`coherence_gate`'s empty-population pass, and my own all-clean degeneracy result in R-21 which
  needed mutation-verification before it meant anything).

**Mutation-verified:** the real pairing matches; the same file with `--max-new 999` appended does not.

#### Manifest verification, complete

| rows | status |
|---|---|
| analysis commands (5) | **executed, reproduce published numbers exactly** (C-13, R-41, R-42) |
| bank regeneration | **byte-identity test** |
| tokenization audit | **re-executed (782071), reproduces R-18 exactly** |
| GPU/API arms | **argsfiles verified against real `argv`, 38/38** |
| claim coverage | **12/12**, checked by script |

**§19-E is now satisfied in fact rather than in prose.** The audit cost four ticks and produced one
real defect (C-13), two missing commands (R-42), and this guard — **all of which existed before the
audit and none of which would have been found by reading the manifest.**

---

### R-42 (06:12) — **Manifest coverage audit: C6 and C7 had NO reproduction command at all. Both now have one, and both reproduce their published numbers exactly. Coverage is 12/12.**

C-13 tested three manifest commands and found a defect; R-41 replaced a prose row with a script.
**This tick asked the prior question: does every claim even HAVE a row?** It did not.

| claim | had a command? |
|---|---|
| C1-C5, C8-C12 | yes |
| **C6** (refusal dose-response, R-22) | ❌ **none** |
| **C7** (demonstration-specificity at `n_examples`=2, R-26) | ❌ **none** |

**Both were computed inline in a shell heredoc and never scripted** — the same "reconstruct a method
from prose" that §19-E forbids and that C-13 had just shown the cost of. **Two of the twelve
paper-level claims were unreproducible except by re-deriving the analysis from the log.**

**`src/boombness/dose_breakdown.py`** (new) covers both, since both are arm-vs-baseline **per dose**.
It reproduces the published numbers **exactly**:

| claim | published | regenerated |
|---|---|---|
| C6 Llama refusal rows by dose | `+0, +3, +9, +14` (monotone) | **`[0, 3, 9, 14]`, monotone True** |
| C6 Qwen3 | `+7, +1, +5, +8` (non-monotone) | **`[7, 1, 5, 8]`, monotone False** |
| C6 Llama controls | flat at/below zero | **legacy `[-1,0,-2,-1]`, respq `[-3,-1,-2,-1]`** |
| C7 at n=2 | demoproc 5/5 attacks; capped 0.67/5; ratio 0.989 | **demoproc −5 of 5; capped mean −0.67; ratio 0.98885** |
| C7 under-matching at n=4 / n=8 | 0.547 / 0.272 | **0.547 / 0.272** |

**What the script enforces**, so the caveats cannot be dropped by whoever runs it next:
* **cell size and margin-in-rows per dose** — at n=40 the margin is **2.1 rows**, and a per-dose
  number without its cell size is not interpretable;
* **both ASR and refusal, always** — C-12 established they are separable, so an arm that moves one
  and not the other is the interesting case and must not be hidden;
* **`control_draw_match_ratio` travels** — R-24/R-26: an under-matched control showing no effect is
  an artifact of the under-matching;
* **monotonicity is reported, not tested** — R-22 was refuted on Qwen3 by a pre-registered
  **endpoint** rule, and re-testing it as monotonicity would quietly change the hypothesis.

**Manifest coverage is now 12/12**, verified by a script rather than by reading. Of the thirteen
manifest rows, **seven have now been executed and confirmed** (`phase1_decomposition`, `kill_route_breakdown`,
`binding_behaviour_bridge`, `rescue_dissociation_table`, `dose_breakdown`, the `tokenization_audit`
re-run as job 782071 reproducing R-18's `rows ok=4560 bad=0 ambiguous=7, violations=0` exactly, plus
bank regeneration via its byte-identity test); the remainder are GPU/API arms whose argsfiles are
committed and were the ones actually run.

---

### R-41 (05:40) — **C9 now has a COMMAND instead of a prose instruction, and it reproduces DR-5's hand audit exactly.**

C-13 established what an untested prose manifest row costs. **The very next row was one:** C9 — the
phase's strongest claim — was documented as *"join the judge dirs by `prompt_id` and read the
`refused` field."* **That is prose, and §19-E forbids exactly that for an important result.**

**`src/boombness/rescue_dissociation_table.py`** (new) emits the whole table, and it **reproduces the
hand audit in DR-5 to the row**:

| cell | n | effect (rows) | margin (rows) | ×margin | control | % of rise |
|---|---|---|---|---|---|---|
| Llama/A | 160 | 18 | 8.3 | **2.16** | **0** | 69.2% |
| Qwen3/A | 160 | 17 | 8.3 | **2.04** | **0** | 81.0% |
| Qwen3/B | 160 | 12 | 8.3 | **1.44** | **0** | 92.3% |
| Llama/B | 160 | 18 | 8.3 | **2.16** | **0** | 58.1% |
| C11 query span | 160 | 25 | 8.3 | **3.00** | **0** | 96.2% |
| C12 demo-24 (`n_examples`=8) | 40 | **4** | **2.1** | **1.92** | **0** | 28.6% |

**The script enforces the discipline rather than relying on me to remember it:**
* **a percentage can never be emitted without `effect_rows` and `effect_x_margin` beside it** — DR-5's
  finding is baked into the artifact and into the printed line, and `PCT_CAVEAT` travels in the JSON;
* **the control is reported per cell and counted** (`n_cells_control_inert`), because a rescue number
  without its below-band control is not evidence of localisation;
* **refusal is read from the judge row's `refused` field** (`kw_refusal`), never the LLM judge;
* malformed specs, **duplicate cell names**, and an **empty four-way intersection** are all refused
  rather than reported as zero.

⚠ **One denominator distinction, so it is not conflated later.** This script's `pct_of_rise_removed`
divides by **(knockout − clean)**. **R-40's 36.4% divided by (knockout − full-demo-patch)** — a
different and, for the size question, more relevant denominator. **The C12 cell therefore reads 28.6%
here and 36.4% in R-40, and both are correct for what they measure.** Neither is a correction of the
other.

**Six tests** pin the behaviour, including that the percentage cannot travel alone and that the
control is never averaged away. **Manifest row replaced with the real command.**

---

### 🔴 C-13 / DR-6 (05:15) — **I EXECUTED the reproduction manifest instead of trusting it, and it found a silent-subsetting defect in `binding_behaviour_bridge`. No published result is affected; the instrument is now guarded.**

§19-E promises *"one command/script path that regenerates its compact analysis artifact"* and
*"no important result should require reconstructing a method from prose."* **That promise had never
been tested.** Testing it is this tick's work.

| manifest command | reproduces? |
|---|---|
| `phase1_decomposition.py` → `p4bdec` | ✅ **byte-identical** (ignoring dir paths) |
| `kill_route_breakdown.py` → `krb` | ✅ **all 8 cells' counts identical** |
| `binding_behaviour_bridge.py` → `bridge` | ❌ **DID NOT REPRODUCE** |

#### The defect

The bridge builds `fam` from `--bank` and the join **silently skips any row whose `prompt_id` the
bank does not know.** Measured:

* the carrot bank's **2736** ids are a **strict subset** of the d10 bank's **4560**;
* so handing it **d10 judge dirs** with the **carrot bank** keeps **96 of 160 rows**…
* …and prints a **complete-looking result with different numbers**: `demoproc` contingency
  **7/41 became 10/38**. **No warning, no row count, nothing.**

**This is the silent-subset class this sprint has already paid for twice** (R-24's under-matched
control, R-26's capped draw), now in an analysis script rather than an intervention.

#### ✅ No published result is affected — verified, not assumed

R-16's and R-17's **actual** pairings were re-checked against the carrot bank:

| run | rows | rows NOT in the bank |
|---|---|---|
| R-16 beh baseline / demoproc | 96 / 96 | **0 / 0** |
| R-17 beh baseline / demoproc | 96 / 96 | **0 / 0** |
| R-16 / R-17 probe baselines | 48 / 48 | **0 / 0** |

**Every published bridge number came from a correctly matched pairing.** And with the guard in place
**R-16 reproduces exactly on all three arms** — `demoproc` 7/41, `legacy` 5/2/37/4, `qpre` 7/33/8.

#### The fix

The bridge now **refuses** any run whose rows are not all in `--bank`, checking **both** the
behavioural and probe populations, **before any arm is read** (refusing later would still emit a
partial artifact). Mutation-verified: the previously-silent mismatch now fails with
`REFUSING: 64 of 160 beh_baseline rows are not in --bank`. Three tests pin the behaviour, including
that the guard covers both populations and runs early.

**Manifest also corrected:** the C5 row now names **which** bank pairs with which judge dirs, since
"pass a bank" was exactly the under-specification that let this happen.

⚠ **The lesson is the method, not the bug:** two of three manifest commands reproduced perfectly, and
the third would have looked fine forever if the manifest had stayed a written promise. **A
reproduction manifest that has never been run is a hypothesis.**

---

### 🔎 DR-5 (04:10, 4h DEEP REVIEW) — **Suite 1377/0. A floor audit of the whole rescue arc in ROWS — and it shows the percentages I have been quoting are INVERTED relative to the evidence.**

**Suite:** `1377 passed, 7 skipped, 0 failed`, serial and exclusive; working tree clean.

**Every rescue-arc claim, restated in rows against the margin in rows:**

| claim | n | knockout | rescue | effect (rows) | margin (rows) | **× margin** | control |
|---|---|---|---|---|---|---|---|
| C9 Llama/A | 160 | 35 | 17 | 18 | 8.3 | **2.16** | **0** |
| C9 Qwen3/A | 160 | 23 | 6 | 17 | 8.3 | **2.04** | **0** |
| **C9 Qwen3/B** | 160 | 15 | 3 | **12** | 8.3 | **1.44** ⚠ | **0** |
| C9 Llama/B | 160 | 32 | 14 | 18 | 8.3 | **2.16** | **0** |
| C11 query span | 160 | 35 | 10 | 25 | 8.3 | **3.00** | **0** |
| **C12 demo-24** | **40** | 15 | 11 | **4** | **2.1** | **1.92** ⚠ | **0** |

**All six clear the margin. Every control is exactly 0 rows.** But two sit under 2×, and one of them is
the cell I have been describing most enthusiastically.

#### 🔴 The percentages are inverted relative to the evidence

| cell | headline % | effect in rows | × margin |
|---|---|---|---|
| Qwen3/B | **92.3%** — the largest | **12** | **1.44 — the smallest** |
| Llama/A | 69.2% — the smallest | **18** | **2.16 — joint largest** |

**The cell with the highest percentage has the weakest absolute evidence, and the cell with the lowest
percentage has the strongest.** The reason is arithmetic and I should have flagged it when I wrote
R-37: **"% of the refusal rise removed" divides by (knockout − clean), and Qwen3/B's clean baseline is
2 rows of 160.** A near-zero denominator inflates the ratio. **92.3% is not a bigger effect than 69.2%;
it is a smaller effect over a smaller rise.**

**Nothing is retracted** — every cell clears its pre-registered margin, and the margin test, not the
ratio, was always the registered quantity (PR-14 explicitly pre-committed recovery percentages as
**not** the test). **But the percentages have been leading every summary table, and they mislead.**
**From here the ledger and handoff carry rows-and-×margin beside every percentage.**

#### What C9 actually rests on

**Not any single cell's magnitude.** It rests on **4/4 replication across two model families and two
demonstration pools**, with **every control at exactly 0 rows** — a specificity result that no single
cell provides and that a percentage cannot express.

#### ⛔ Recommendation on continuing this arc

**The arc's returns are falling and its numbers are thinning**: 18 → 17 → 12 → 18 → 25 → **4** rows.
**C12 rests on 4 rows against a 2.1-row margin.** PR-18 already forbade a third arm to sharpen it, and
that was right. **Further single-cell rescue arms on this bank are not justified by current evidence**
— the next real gain needs the longer-context bank (R-25) or a benign-register concept (R-27), both
**bank-design changes awaiting the user's go-ahead**, not more patches.

---

### ⚖️ R-40 (03:42) — **PR-18: at MATCHED SIZE the two position sets behave completely differently, so R-39's contrast is NOT a size artifact. But the outcome satisfies TWO of my own outcome definitions at once — a defect in PR-18 that I am owning rather than resolving in my favour.**

**Artifacts:** `p10_demo24_L14` (781930) / `p10_demo24_L5` (781931); judging `p10j_*` (781956).
**Preconditions:** `fired` **80/80**, `rescue_n_positions_requested = 24` and `n_rescue_positions = 24`
on **every** row, all rows `n_examples = 8`, knockout live, no violations. **Provenance 80/80.**
**PR-18 committed at `d9669e82` first.**

**All arms restricted to the same 40 rows (`n_examples = 8`). ⚠ At n = 40 the 0.0521 margin is 2.1
rows — it is doing much less work here than at n = 160.**

| arm | positions | ASR | refusal rows | refusal |
|---|---|---|---|---|
| clean baseline | — | 0.2500 | 1/40 | 0.0250 |
| knockout-only | — | 0.0000 | **15/40** | 0.3750 |
| rescue FULL demo | 91-128 | 0.0250 | **4/40** | 0.1000 |
| **rescue DEMO, 24 positions** | **24** | **0.0000** | **11/40** | **0.2750** |
| rescue DEMO 24, L5 control | 24 | 0.0000 | **15/40** | 0.3750 |
| rescue QUERY, 24 positions (R-39) | **24** | **0.0500** | **2/40** | **0.0500** |

#### ✅ The size confound is answered: identity, not count

**The two 24-position patches — same count, same layer, same rows, same donor — do completely
different things:**

| 24 positions from… | refusal removed | ASR |
|---|---|---|
| **demonstration block** | 4 rows (0.1000) | **+0.0000 — no attack restored** |
| **query span** | **13 rows (0.3250)** | **+0.0500 — attack partially restored** |

**R-39's contrast survives size-matching.** A 24-position query patch removes **more than three times**
the refusal of a 24-position demo patch **and** restores attack, which the demo patch does not. **The
selectivity of the demonstration positions is a property of WHICH positions they are.**

Note also: **24 query positions remove more refusal (0.3250) than 91-128 demo positions do (0.2750).**
The query span is **more potent per position on both effects** — it is downstream and aggregates.

#### ⛔ My pre-registration had overlapping outcomes, and I am not choosing the flattering one

PR-18 defined **A** as *"still removes refusal > 0.0521 **and** still fails to restore ASR"* and **C**
as *"removes refusal but by markedly less than the full patch"*. **This result satisfies both.** It
clears the threshold (0.1000 vs 0.0521) with ASR untouched (**+0.0000**) — **and** it achieves only
**36.4%** of the full patch's refusal removal (4 rows of 11).

**Those definitions should have been mutually exclusive and were not. That is a defect in PR-18, not
a finding**, and picking A because it reads better would be exactly the failure pre-registration
exists to prevent. **Both are reported:**

> **A on the threshold, C on the magnitude.** Position identity is established — a size-matched demo
> patch behaves nothing like a size-matched query patch. **But the demo effect also clearly scales
> with count**: 24 of ~114 positions (21%) buys 36.4% of the effect. **It is identity AND count, not
> identity alone**, and no claim of all-or-none locality is made.

⚠ **n = 40; the demo-24 refusal effect is 4 rows against a 2.1-row margin** — it clears by under two
rows and is the thinnest number in this arc. ⚠ The L5 control is **exactly inert again** (15 → 15).
⚠ Llama only. ⚠ **No third arm will be run to sharpen this**, per PR-18.

---

### PR-18 (03:15) — **Pre-registered: SIZE-MATCHING the two patches. Is R-39's contrast about which positions are restored, or just how many?**

R-39 compared a **24-position** query patch against a **9-128-position** demo patch (median 43) and
**could not separate position identity from position count.** I flagged that in R-39 rather than
leaving it; this settles it.

**⛔ First, why the free version of this test does not work.** The obvious move is to condition R-35 on
`n_examples`, since the demo patch spans **9-18 positions at n=1** (below the query span's 24) up to
**91-128 at n=8**. **That analysis is invalid here**, and running it would have been a mistake:
**R-22 measured the knockout's own refusal rise at `n_examples = 1` as exactly `+0.0000`.** At small
patch sizes **there is no refusal restoration for a rescue to undo** — so patch size and effect size
are **the same variable**, and a null at n=1 would be uninterpretable. **No re-cut of existing data can
answer this; it needs a new arm.**

**The design.** At **`n_examples = 8` only** — the best-powered cell, where the knockout's refusal rise
is **+0.3500** (R-22) and the demo block is **91-128 positions** — donate **exactly 24 randomly drawn
demonstration positions**, size-matched to the query span. Draw is **seeded by `prompt_id`**, so each
row always donates the same subset and the draw is auditable after the fact; a row with fewer than 24
positions is **REFUSED, never silently under-matched** (R-24/R-26 already paid for that lesson).

**Arms (Llama, d10, `--n-examples 8`, 40 rows):** `p10_demo24_L14` (primary) and `p10_demo24_L5`
(below-band control). Comparators, all same-session: knockout-only and the **full** demo patch, both
restricted to the same `n_examples = 8` rows.

**Outcomes, fixed now:**

| outcome | pattern | reading |
|---|---|---|
| **A — identity** | 24 demo positions still remove refusal **> 0.0521** and still fail to restore ASR | **Position identity, not count.** R-39's contrast stands and C9 is size-robust |
| **B — count** | 24 demo positions remove **no** refusal (within margin of knockout) | **The demo patch's effect needed its size.** R-39's identity reading is **withdrawn**, and C9 must be restated as requiring the whole block |
| **C — partial** | removes refusal but by markedly less than the full patch | Report the fraction; **claim neither identity nor count** |

**⛔ Pre-committed.** This is a **40-row cell** — a quarter of the usual n. `MARGIN_VS_BASELINE = 0.0521`
is **2.1 rows at n=40**, so **the margin is doing much less work here and I will say so beside every
number.** The knockout's n=8 refusal rise of +0.3500 (14 rows of 40) is the largest available, which is
why this cell and no other. **If the result is Outcome C, no third arm is run to break the tie** — a
tie broken by a third look is not a result.

---

### ⚖️ R-39 (02:47) — **PR-17 OUTCOME A: the attack damage IS in the query span. But the risk I flagged against my own C9 MATERIALISED — the query patch restores BOTH effects, so this is a SINGLE dissociation, not a double one.**

**Artifacts:** arms `p9_rescue_qpos_L14` (781849) / `p9_rescue_qpos_L5` (781850); judging `p9j_*`
(781899). **Provenance:** `openai/gpt-4o-mini` **320/320**, hash joins **320/320**. `fired` **320/320**,
`rescue_positions = query`, **24 positions on every row**, knockout `scope_live = 1.0`.
**PR-17 committed at `9b20e40e` before the arms existed.**

| arm | ASR | refusal rows | refusal |
|---|---|---|---|
| clean baseline | 0.1562 | 9/160 | 0.0563 |
| knockout-only | 0.0063 | 35/160 | 0.2188 |
| rescue **DEMO** positions L14 (R-35) | 0.0312 | 17/160 | 0.1062 |
| **rescue QUERY positions L14 (new)** | **0.0625** | **10/160** | **0.0625** |
| rescue QUERY positions L5 (control) | 0.0187 | 35/160 | 0.2188 |

**ASR: `L14 − knockout = +0.0563` > 0.0521; control `+0.0125`, inert. → OUTCOME A.**
**The attack damage is reachable from the query span and was not reachable from the demonstration
positions.** That is a genuine localisation: two position sets, same layer, same donor, same knockout,
opposite results on ASR.

#### ⛔ But read the recovery fractions, not just the verdict

* **ASR recovery is 37.5%**, not restoration. `|query − clean| = 0.0937`, **still above margin** — the
  attack comes back **partially**. (Demo positions: 16.6%.) **"Outcome A" means it cleared the
  pre-registered threshold, NOT that the attack was restored.**
* **The refusal risk I pre-registered as a threat to C9 HAPPENED.** The query patch moves refusal by
  **0.1562 — MORE than the demo patch's 0.1125** — taking it **35 → 10 rows**, i.e. **96.2% of the
  rise removed** and `|query refusal − clean| = 0.0062`, **within margin of clean.**

#### 🔴 What this costs, stated plainly

**This is NOT a double dissociation, and I am not going to write it as one.** The picture is:

| position set patched | refusal | attack |
|---|---|---|
| **demonstration block** | restored (69.3%) | **NOT restored** (16.6%, within margin of knockout) |
| **query span** | restored (96.2%) | **partially restored** (37.5%, clears margin) |

**The query span restores everything it touches.** It sits downstream and aggregates; a patch there is
**not selective** and cannot be used to argue that attack and refusal have separate substrates.

**C9 is NOT weakened as stated** — its claim is about the **demonstration positions**, and there the
selectivity is intact and replicated 4/4: **restoring them gives back the refusal and not the attack.**
**What is now excluded is the stronger claim I never made but might have drifted toward** — that the
two effects live at *separate loci*. **They do not. One locus is selective; the other is not.**

**The defensible mechanistic statement, and it is narrower than last tick's:**

> **By the top of the knockout band, the demonstration positions still carry what the refusal decision
> needs but no longer carry what the attack needs; the query positions carry both. Restoring the
> demonstrations gives back the refusal alone — restoring the query span gives back some of each.**

⚠ Llama only; PR-17 authorised cross-model only on Outcome A, which holds — **but given the
non-selectivity, replicating a non-specific patch is low value and is NOT being launched.** ⚠ Query
span is a constant 24 positions vs the demo block's 9-128; **the two patches are not size-matched**,
and a 24-position patch achieving more refusal removal than a 43-median-position one is itself
evidence that position *identity*, not count, is doing the work. ⚠ Truncation per DR-2.

---

### PR-17 (02:10) — **Pre-registered: if the attack damage is NOT in the demonstration positions, is it in the QUERY positions that read from them?**

R-35 returned **Outcome C** on Llama: handing back the clean demonstration activations at the top of
the band restores the refusal but **not** the attack. **So the ASR damage is somewhere else** — and
the obvious somewhere is the positions the demonstrations are read *into*: the query span, which
`demo_processing_only` never touches directly and can only damage **indirectly**, through what those
positions attend to.

**This is a different POSITION SET at the same layer — not a layer sweep.** PR-13 forbade scanning
layers until one rescues; this does not scan anything. `--rescue-positions query` donates
`query_span_positions` (the harmful request onward) instead of the demonstration block, at the **same
L14**, from the **same clean donor**, under the **same knockout**.

**Arms (Llama, d10 bank, 160 rows):** `p9_rescue_qpos_L14` (primary) and `p9_rescue_qpos_L5`
(below-band control). Baseline `p4bA` and knockout `p4b_demo_processing_only` already exist **in the
same judging session as R-35's arms**, so this cell is same-session, unlike R-38's.

**Outcomes, fixed now:**

| outcome | pattern | reading |
|---|---|---|
| **A — the damage is in the query span** | `L14 ASR − knockout > +0.0521`, and L5 does not | The knockout removes the attack by corrupting what the query positions carry, **not** the demonstrations' own representation |
| **B — null** | `\|L14 ASR − knockout\| ≤ 0.0521` | Neither position set at this layer holds it. **Combined with R-35 that is a substantive negative: the ASR effect is not recoverable by restoring either span at the top of the band** |
| **C — invalid** | L5 recovers as much as L14 | Nonspecific patch; no claim |

**⛔ Pre-committed.**
* **Outcome B is a real result and will be reported as one, not buried.** Two position sets, both
  restored, neither bringing the attack back, is informative about where the effect is *not*.
* **Refusal is reported beside ASR** — and note the prediction differs: patching the **query** span
  should NOT undo the refusal restoration if the refusal effect lives in the demonstration positions
  (R-35/36/37/38). **A query-span patch that also removes the refusal rise would weaken C9's
  positional specificity**, and I flag that risk before running.
* **Preconditions:** `fired` true on every row (`n_rescue_positions` now recorded per row too), judge
  pinned, truncation reported.
* **Llama only.** Cross-model only if Outcome A.

**Smoke before sweep**, per the standing rule — 8 rows first, to confirm the query span resolves and
the patch fires on a position set that is **not** the demo block.

---

### 🏆🏆🏆 R-38 (01:20) — **PR-16 CONFIRMS. The 2 × 2 over model family × demonstration pool is COMPLETE: in all four cells the patch gives back the refusal, and in all four the below-band control moves it by EXACTLY 0.0000.**

**Artifacts:** arms `p8b_rescue_L14` (781643) / `p8b_rescue_L5` (781644); judging `p8bj_*` (781727).
**Provenance:** `openai/gpt-4o-mini` on **320/320**, hash joins **320/320**; bank B content-verified,
`matchesA = 0`; `fired` **320/320**, layers 14 and 5. **PR-16 committed at `55c5e66b` first.**

| arm | ASR | refusal rows | refusal |
|---|---|---|---|
| clean *(R-29, other session)* | 0.1688 | 1/160 | 0.0063 |
| knockout *(R-29, other session)* | 0.0375 | **32/160** | **0.2000** |
| **rescue L14 (primary)** | 0.0688 | **14/160** | **0.0875** |
| rescue L5 (control) | 0.0437 | **32/160** | **0.2000** |

**Condition 1 — HOLDS.** `|L14 − knockout| = 0.1125`, **2.2× margin**, less refusal: **32 → 14 rows**.
**Condition 2 — HOLDS.** Control at **exactly 0.0000** — **32 → 32 rows**.

#### ✅ The completed design

| cell | model | pool | knockout → rescue | \|gap\| | refusal rise removed | control |
|---|---|---|---|---|---|---|
| R-35 | Llama-3.1-8B | A | 35 → 17 | 0.1125 | 69.2% | **0.0000** |
| R-36 | Qwen3-14B | A | 23 → 6 | 0.1062 | 81.0% | **0.0000** |
| R-37 | Qwen3-14B | B | 15 → 3 | 0.0750 | 92.3% | **0.0000** |
| **R-38** | **Llama-3.1-8B** | **B** | **32 → 14** | **0.1125** | **58.1%** | **0.0000** |

> **Two model families × two demonstration pools sharing no sentences. Four for four on the effect,
> four for four on the control being exactly inert.**

#### 🔍 The cross-session caveat I declared — and what the data says about it

PR-16 flagged, before reading, that this cell's baseline and knockout come from a **different judging
session** than its rescue arms, making it the weakest of the four by construction.

**The control arm settles it.** `p8b_rescue_L5` was judged in the **new** session and returns
**32/160** refusals — **identical, to the row, to the knockout arm's 32/160 from the old session.**
**The very comparison the caveat was about is reproduced exactly across sessions**, so for this metric
the session boundary moved nothing.

**I am not withdrawing the caveat** — one metric agreeing across two sessions is not a general licence,
and the judge's 78/96 binary drift was measured on a different quantity. **But the cell is no longer
"weakest by construction" in the way I predicted, and saying so is the honest update.** The
`kw_refusal` detector is deterministic, which is very likely why: **it is the one instrument in this
phase that cannot drift between sessions.**

⚠ **58.1% is the lowest of the four** — the effect size varies across cells (58-92%) even though every
cell clears its margin. **The margin test replicates 4/4; the magnitude does not, and should not be
quoted as a single number.** ⚠ The ASR column is not counted here (PR-16), and R-37 already closed the
ASR rescue.

---

### 🔎 DR-4 (00:45, 4h DEEP REVIEW) — **Suite 1372/0. All three dissociation cells recomputed exactly from raw rows. One published figure corrected (92.4% → 92.3%), and one near-miss on judge-directory namespacing.**

**Suite:** `1372 passed, 7 skipped, 0 failed`, serial and exclusive; `outputs/ reports/ data/` clean.

**Independent recomputation of the headline, from raw judge rows, in ROWS rather than rates:**

| cell | n | clean | knockout | rescue | control | \|rescue−knock\| | \|control−knock\| | removed |
|---|---|---|---|---|---|---|---|---|
| Llama/A | 160 | 9 | 35 | **17** | 35 | **0.1125** | **0.0000** | 69.2% |
| Qwen3/A | 160 | 2 | 23 | **6** | 23 | **0.1062** | **0.0000** | 81.0% |
| Qwen3/B | 160 | 2 | 15 | **3** | 15 | **0.0750** | **0.0000** | **92.3%** |

**Every rescue gap clears the margin; every control gap is EXACTLY 0.0000 — not "small", exact.** The
control arms produce byte-identical refusal counts to knockout-only in all three cells, which is the
strongest form the specificity check can take.

**Floor / saturation:** finest step `1/160 = 0.00625`, margin = 8.3 rows; the three gaps are **18, 17
and 12 rows** — **1.4-2.2× the margin.** Not at the floor, not saturated.

#### ✏️ Correction: 92.4% → 92.3%

R-37 published **92.4%** for pool B's refusal-rise removal. **Recomputed from rows it is 12/13 =
92.3%.** The 92.4 came from dividing **rounded rates** (`(0.0938−0.0187)/(0.0938−0.0125)`) rather than
counts. **Difference: 0.07 percentage points, changes nothing** — but it is a published figure that did
not reproduce exactly, so it is corrected in place rather than left. **Row counts are the honest
denominator here and rates should not have been rounded before dividing.**

#### ⚠ Near-miss: judge-prefix namespacing

`ls outputs/boombness/judge/p7j_*` returns **five** directories, not two: `p7j_rescueL14`,
`p7j_rescueL5` — **and `p7j_p7A`, `p7j_p7N`, `p7j_p7W` from a different sprint on 2026-08-24.** The
prefix `p7j` was reused. **No collision occurred** (max directories per tag = **1** across all seven
prefixes this phase created: `p4bj q4bj p5j p6bj p7j q7j q6bj`), because the *tags* differ — but a
glob-by-prefix analysis would have silently pooled a prior sprint's arms with this one's.
**Every analysis in this phase joins by explicit run directory, not by prefix glob**, which is why it
did not bite. **Recorded so the next person globbing `p7j_*` knows it is not a clean namespace.**

**Provenance re-confirmed:** 0 duplicate tags across all seven prefixes; bank B content-verified with
`matchesA = 0` on all four `q6b` arms (R-37).

---

### PR-16 (00:38) — **Pre-registered: the fourth cell. Llama × pool B completes the model × pool design for the causal dissociation.**

The dissociation holds in **Llama/A** (R-35), **Qwen3/A** (R-36) and **Qwen3/B** (R-37). **The missing
cell is Llama × pool B**, and filling it turns three scattered replications into a complete **2 × 2 over
model family and demonstration pool** — the design that separates "this is a property of the mechanism"
from "this is a property of Llama, or of pool A".

**Cheap by construction:** Llama pool-B **baseline and knockout already exist and are already judged**
(`p6bj_A`, `p6bj_demoproc`, from R-29). **Only two new arms are needed** — `p8b_rescue_L14` (781643)
and the below-band control `p8b_rescue_L5` (781644). **Two arms, not four**, which also keeps
concurrent 14B/8B loads at two and avoids the NFS contention logged at 23:40.

**⚠ One thing I am NOT doing, and it matters:** the baseline and knockout come from a **different
judging session** than the rescue arms will. Every prior cell measured all arms in one session. **The
judge's own re-scoring drift is 78/96 binary agreement across sessions**, and PR-3's margin
`MARGIN_VS_BASELINE = 0.0521` was measured to absorb exactly that. **So this cell is reported as
CROSS-SESSION and is the weakest of the four by construction**, and I am saying so before reading it
rather than after.

**Conditions, identical to PR-14's (no new thresholds invented for a fourth look):**
1. `|L14 refusal − knockout refusal| > 0.0521`, direction = **less refusal**.
2. `|L5 refusal − knockout refusal| ≤ 0.0521` — the below-band control is inert.

**Refuted if** 1 fails. **Invalid** if 2 fails.

**⛔ Pre-committed:**
* **The ASR column does not count here either.** R-37 killed the ASR rescue on its own confirmatory
  test; **a Llama pool-B ASR number is not a second chance for it.**
* **No comparison to clean refusal** — declined on Llama/A and Qwen3, declined here in advance.
* **Preconditions:** `rescue_liveness.fired` true on every row of both arms or the arm is
  **UNMEASURED, not null**; judge pinned; truncation reported.
* **If this holds, the claim becomes "3 of 4 cells same-session plus 1 cross-session"** — not "4/4
  clean". The asymmetry in evidence quality travels with the result.

---

### ⛔ R-37 (00:25) — **PR-15 DOES NOT CONFIRM. The Qwen3 ASR rescue fails its own pre-registered threshold on an independent pool — so the unregistered observation is NOT promoted. The REFUSAL dissociation replicates a third time.**

**Artifacts:** arms `q6b*` (781410-781413), judging `q6bj_*` (781548).
**Provenance:** `openai/gpt-4o-mini` on **640/640**, hash joins **640/640**. Bank B verified at content
level with **`matchesA = 0`** on all four arms. Rescue `fired` **160/160** on both rescue arms, layers
17 and 5. **PR-15 committed at `c7598bf7` before the arms existed.**

| arm | ASR | refusal rows | refusal |
|---|---|---|---|
| clean baseline | 0.1375 | 2/160 | 0.0125 |
| knockout-only | 0.0437 | **15/160** | **0.0938** |
| **rescue L17 (primary)** | **0.0875** | **3/160** | **0.0187** |
| rescue L5 (control) | 0.0312 | **15/160** | **0.0938** |

| condition | value | verdict |
|---|---|---|
| **1 — ASR rescue** | `L17 − knockout = +0.0437`, needed **> 0.0521** | **FAILS** |
| 2 — control inert | `|L5 − knockout| = 0.0125` | HOLDS |
| 3 — refusal dissociation | `|L17 − knockout| = 0.0750`, less refusal | HOLDS |

#### ⛔ The ASR rescue is NOT promoted

On pool A it was **+0.0625** (above margin); on pool B it is **+0.0437** (below). **It misses the
pre-registered threshold by 0.0084 — about 1.3 rows of 160.** The direction is the same in both pools
and the magnitudes differ by **3 rows**, so this is **not a clean refutation either** — it is exactly
what an underpowered effect looks like when you demand it clear a threshold twice.

**By the rule I wrote before seeing any of it, the Qwen3 ASR rescue is NOT established, and it does not
enter the claim table.** It stays an **UNREGISTERED OBSERVATION that failed its confirmatory test.**

> **This is the pre-registration doing precisely the job it exists for.** In R-36 the ASR column was
> the most exciting number on the page, sitting in a column I had declared irrelevant. Had I claimed it
> then, this tick would have been a retraction. Instead it was never a claim.

**Not rescued, and I am not looking for a rescue.** No layer sweep, no third pool, no relaxed margin.
`MARGIN_VS_BASELINE = 0.0521` was measured from re-judge spread (PR-3), not chosen; **an effect that
needs the margin moved is not an effect.**

#### 🏆 What DID replicate, for the third time

**Condition 3 holds and holds hard.** `L17` removes **92.3%** of pool B's refusal rise —
**15 rows → 3** — while the below-band control moves it by **exactly 0.0000** (15 → 15).

**The causal dissociation now stands in three independent settings:**

| setting | model | pool | refusal rise removed | control |
|---|---|---|---|---|
| R-35 | Llama-3.1-8B | A | **69.2%** | 0.0000 |
| R-36 | Qwen3-14B | A | **81.0%** | 0.0000 |
| **R-37** | **Qwen3-14B** | **B** | **92.3%** | **0.0000** |

**Two model families, two demonstration pools sharing no sentences, and in every one the same patch
gives back the refusal while the below-band control at the same positions does nothing.**

⚠ Pool B knockout refusal is **15/160** and the rescued arm **3/160** — small counts; the percentages
are ratios of few rows and the margin test, not the ratio, is what carries. ⚠ Truncation per DR-2.

---

### PR-15 (23:05) — **Pre-registered: the confirmatory test of R-36's UNREGISTERED OBSERVATION — does the Qwen3 ASR rescue survive on an INDEPENDENT demonstration pool?**

R-36 recorded, and refused to claim, that on Qwen3 the L17 patch appears to restore the **attack**
(knockout 0.0437 → 0.1062 vs clean 0.1313), where the same design on Llama gave a null. R-36 stated
what claiming it would require: **its own pre-registration fixing margin and direction, plus an
independent replication.** This is that pre-registration, written before the arms exist, and the
replication runs on **pool B — the bank whose 40 demonstration pools share ZERO sentence sets with
pool A** (R-28).

**Why pool B and not a re-run.** Re-running the same bank would test session noise, not the finding.
**Pool B changes the demonstration text entirely while holding the design, the model, the band and the
patch fixed** — so a survival there is a statement about the mechanism rather than about these
particular demonstrations.

**Arms (Qwen3-14B, bank B, band 7-17, 160 rows each):** `q6bA` (clean), `q6b_demo_processing_only`
(knockout-only), `q6b_rescue_L17` (primary), `q6b_rescue_L5` (below-band specificity control).
**All four are new** — Qwen3 has never been run on pool B, so the baseline and knockout cannot be
borrowed and are measured in the same session as the arms.

**The claim, and it CONFIRMS only if ALL THREE hold:**
1. **`L17 ASR − knockout ASR > +0.0521`** — the patch restores attack, direction fixed in advance.
2. **`|L5 ASR − knockout ASR| ≤ 0.0521`** — the below-band control does **not**.
3. **`|L17 refusal − knockout refusal| > 0.0521`, direction = less refusal** — the refusal
   dissociation (R-36's *registered* result) also reproduces on pool B, so the ASR effect is not
   arriving in place of it.

**Refuted if** condition 1 fails. **Invalid (no claim either way) if** condition 2 fails — a control
that also rescues means the patch is nonspecific on this bank.

**⛔ Pre-committed limits.**
* **This tests ONE model.** Even on success the ASR rescue is **Qwen3-only**, and Llama's Outcome C
  (R-35) stands unchanged. **The cross-model asymmetry is the finding, not an inconvenience to
  resolve by finding a Llama layer that works** — no Llama layer sweep will be run.
* **`|L17 − clean|` is NOT a test here.** On Llama that comparison cleared its margin by a third of a
  row and I declined it; declining it again, in advance.
* **Preconditions:** `rescue_liveness.fired` true on every row of both rescue arms or the arm is
  **UNMEASURED, not null**; judge pinned to `openai/gpt-4o-mini`; truncation reported beside every
  number.
* **If this confirms, it is still ONE pool-pair on ONE model** and will be labelled replicated, not
  established.

---

### 🏆🏆🏆 R-36 (22:50) — **PR-14 PASSES BOTH CONDITIONS: the causal dissociation replicates on Qwen3. And the ASR column shows something I pre-committed NOT to claim — so I am not claiming it.**

**Artifacts:** arms `q7_rescue_L17` (781290) / `q7_rescue_L5` (781291); judging `q7j_*` (781361).
**Provenance:** `openai/gpt-4o-mini` on **320/320**, hash joins **320/320**.
**Precondition met:** `fired` on **320/320** rows, `n_positions_written` 9/43/128, layers 17 and 5 as
specified, knockout `scope_live = 1.0`, no violations. **PR-14 committed at `34cfba52` first.**

| arm | ASR | refusal rows | refusal |
|---|---|---|---|
| clean baseline | 0.1313 | 2/160 | 0.0125 |
| knockout-only | 0.0437 | **23/160** | **0.1437** |
| **rescue L17 (primary)** | 0.1062 | **6/160** | **0.0375** |
| rescue L5 (control) | 0.0250 | **23/160** | **0.1437** |

**Condition 1 — HOLDS.** `|L17 − knockout| = 0.1062`, **2× the margin**, in the pre-specified direction
(**less** refusal): **23 rows → 6**.
**Condition 2 — HOLDS.** The below-band control moves refusal by **exactly 0.0000** — 23 → 23 rows.
✅ **R-35's causal dissociation REPLICATES on a second model family.**

*(Descriptive, not the test: L17 removes **81.0%** of Qwen3's refusal rise; Llama was 69.2%.)*

#### ⛔ The ASR column, reported and NOT claimed

**On Qwen3 the same patch also appears to restore the attack:** knockout **0.0437** → L17 **0.1062**,
against a clean baseline of **0.1313**. That is `|L17 − knockout| = 0.0625` (**above** the 0.0521
margin) and `|L17 − clean| = 0.0251` (**within** it) — **the shape of PR-13's Outcome A**, on the model
where Llama gave **Outcome C**. The L5 control is inert on ASR too (`|L5 − knockout| = 0.0187`).

**PR-14 pre-committed, before any of this was visible:** *"The ASR column… a Qwen3 ASR rescue would be
a new finding requiring its own pre-registration, not a bonus read off this one."*

**So it is not claimed.** It is the most interesting number produced this tick, and **that is exactly
why the rule exists** — a finding discovered in a column I declared irrelevant, on a single model,
with no pre-registered test, is the classic route to an unreproducible headline. **Recorded as an
UNREGISTERED OBSERVATION.**

**What it would take to claim it:** its own pre-registration fixing the margin and direction, an
independent replication (pool B is available and costs two arms), and an account of why Llama and
Qwen3 differ — because **as it stands the phase's causal picture is model-dependent on ASR while
being model-independent on refusal**, and that asymmetry is itself the thing to explain.

#### What is now established across both models

> **Handing back the clean demonstration activations at the top of the knockout band substantially
> undoes the REFUSAL restoration — 69.2% on Llama, 81.0% on Qwen3, both >2× margin — while a
> below-band control at the same positions does nothing at all (0.0000 on both models).**

⚠ Qwen3 clean refusal is **2/160**; the arms' refusal counts (23, 6) are small. ⚠ Truncation carried
per DR-2. ⚠ One layer pair per model, **no layer sweep** (PR-13/PR-14).

---

### PR-14 (22:05) — **Pre-registered: does R-35's CAUSAL dissociation replicate on Qwen3?**

R-35 is the phase's first causal separation of the two effects and it is **Llama-only**. C1 and C2 are
both cross-model; **their causal version must be too, or it is a single-model curiosity.**

**Note on PR-13's cross-model clause.** PR-13 said cross-model follows "only if Outcome A or B holds",
i.e. if the **ASR** rescue worked. It did not — Outcome C. **But the finding that emerged is the
refusal result, which PR-13 explicitly pre-authorised as reportable** ("a rescue could restore one and
not the other, and that dissociation is itself a result"). **I am therefore replicating the refusal
dissociation, not the ASR rescue, and saying so before reading anything.**

**Arms (Qwen3-14B, d10 bank, 160 rows each), band 7-17 as in every prior Qwen3 arm:**
* **`q7_rescue_L17`** — primary. Rescue at **layer 17**, the top of Qwen3's knockout band (the
  positional analogue of Llama's L14 at the top of 6-14).
* **`q7_rescue_L5`** — **below-band specificity control** (Qwen3's band starts at 7).

**Replication requires BOTH:**
1. **Refusal:** `|L17 − knockout|` **exceeds** `MARGIN_VS_BASELINE = 0.0521`, in the direction of
   *less* refusal — i.e. the patch removes a substantial part of Qwen3's refusal rise (+0.1312, R-20).
2. **Specificity:** `|L5 − knockout|` stays **within** 0.0521 — the below-band control does not.

**Refuted if** the L17 patch leaves refusal within margin of knockout-only, **or** if L5 moves it as
much as L17.

**⛔ Pre-committed as NOT counting:**
* **The ASR column.** Llama gave Outcome C and there is no reason to expect otherwise; **a Qwen3 ASR
  rescue would be a new finding requiring its own pre-registration, not a bonus read off this one.**
* **Any comparison to CLEAN refusal.** R-35's clean comparison cleared the margin by **a third of a
  row** and I declined it there; **I decline it here in advance**, whichever way it falls.
* **Recovery percentages** as headline numbers — 69.2% on Llama is a ratio of two small row counts.
  The pre-registered test is the margin comparison, not the ratio.

**Preconditions, same as PR-13:** `rescue_liveness.fired` true on **every row of both arms** or the arm
is **UNMEASURED, not null**; judge pinned; truncation reported beside every number.

---

### 🏆🏆🏆 R-35 (21:57) — **PR-13 OUTCOME C on ASR — and the refusal column separates. Handing back the clean demonstration activations UNDOES 69% OF THE REFUSAL RESTORATION WHILE LEAVING THE ATTACK REMOVAL INTACT. The two effects have different substrates, shown causally.**

**Artifacts:** arms `p7_rescue_L14` (781211) / `p7_rescue_L5` (781212); judging `p7j_*` (781255).
**Provenance:** `openai/gpt-4o-mini` on **320/320** rows, hash joins **320/320**.
**PR-13 precondition met:** `rescue_liveness.fired` on **320/320** rows, `n_positions_written`
9/43/128 identical at both layers, knockout `scope_live = 1.0`, no violations.
**PR-13 was committed at `8ab1eb05` before either job existed.**

| arm | ASR | vs clean | vs knockout | **refusal** |
|---|---|---|---|---|
| clean baseline | 0.1562 | — | +0.1500 | 9/160 = 0.0563 |
| knockout-only | 0.0063 | −0.1500 | — | **35/160 = 0.2188** |
| **rescue L14 (primary)** | 0.0312 | −0.1250 | **+0.0250** | **17/160 = 0.1062** |
| rescue L5 (control) | 0.0125 | −0.1437 | +0.0063 | **35/160 = 0.2188** |

#### On ASR: OUTCOME C — NULL

`|L14 − knockout| = 0.0250`, **inside the 0.0521 margin.** The rescue recovers **16.7%** of the
knockout's ASR effect and is **statistically indistinguishable from not rescuing at all.**

> **The information the knockout destroys to remove the attack is NOT carried in the demonstration
> positions' residual stream at the top of its own band.** Handing those activations back, verifiably
> and per-position, does not bring the attack back. **The damage travels by another route.**

#### 🔴 On refusal: the same patch nearly abolishes the effect

`|L14 − knockout| = 0.1125`, **more than 2× the margin.** The rescue removes **69.2%** of the
knockout's refusal rise — **35 rows → 17** — and the **L5 below-band control moves it by exactly
0.0000 (35 → 35 rows)**, which is what a specificity control must do.

> **One intervention, one layer, one set of positions. It gives back the refusal and does not give
> back the attack.**

**This is the third independent demonstration of C-12, and the first CAUSAL one.** R-19/R-20 showed
the two effects co-occur; R-23 showed they are dose-independent; **R-35 shows a targeted intervention
can restore one without restoring the other.** Correlational dissociation has become a causal one.

#### ⚠ Where the numbers are thin, stated plainly

* **`|L14 refusal − clean refusal| = 0.0500` clears the 0.0521 margin by 0.0021 — about a THIRD OF ONE
  ROW** of 160. **"Restored to clean levels" is therefore NOT a claim I am making.** The defensible
  claim is the one against knockout-only (0.1125, >2× margin): **the rescue substantially undoes the
  refusal restoration.** Whether it goes all the way back to clean is below this instrument's
  resolution.
* **`rescue L14` truncates more than any other arm** — 130/160 at the 192-token cap vs 116 for
  knockout-only and 93 for clean (DR-2's limitation, carried).
* **Llama only; one layer pair; no layer sweep was run**, per PR-13 — so "L14 specifically" is not
  established against layers 6-13, only against L5 and against not patching.
* Outcome **D was tested and not triggered**: `|L5 − L14| = 0.0187`, and L5 does not recover, so the
  patch is not nonspecific.

---

### R-34 (21:12) — **Smoke `781168` re-read under the fixed code: the rescue hook is PROVABLY live from the artifact, not by inference. Sweep submitted (781211 / 781212).**

**Run dir:** `outputs/boombness/score_behavior/p7smoke_rescue_L14_20260825_204132_870233`.

| recorded field | value |
|---|---|
| rows carrying `rescue_liveness` | **8 / 8** |
| `fired` | **8 / 8** |
| `n_positions_written` (min / median / max) | **11 / 43 / 123** |
| `n_forward_calls` | 192 on every row |
| `rescue_layer` / `rescue_donor` | `14` / `clean` on every row |

**The `n_positions_written` spread is the check that matters.** It runs **11 → 123** across eight rows
drawn from `n_examples ∈ {1,2,4,8}` — **it tracks the demonstration block's own size**, exactly as a
correct per-position donor must, and is not a constant. A patch writing a fixed count, or writing
nothing, or writing everywhere, would all be visible here and none of them is what happened.
`n_forward_calls = 192` with a single write per row confirms the write lands at **prefill** and the
hook correctly declines the 191 decode steps (where `seq_len = 1` is past every donor position).

**R-32's defect is closed by evidence rather than by assertion:** the run now says what it did.

**Sweep submitted under PR-13**, committed at `8ab1eb05` **before either job existed**:
`p7_rescue_L14` (**781211**, primary) and `p7_rescue_L5` (**781212**, the below-band specificity
control). 160 rows each, Llama, d10 bank, `demo_processing_only` 6-14.

**Nothing is read until both land, judging completes, and `rescue_liveness.fired` is verified true on
every row of both arms** — PR-13 makes that a precondition, not a courtesy.

---

### PR-13 (21:10) — **Pre-registered before any rescue number is read: what a rescue would and would not demonstrate, and the control that separates the two.**

**The gate is open** (R-33: identity control 8/8 byte-identical) and **the hook is now provably live**
(smoke `781168`: `fired = 8/8`, `n_positions_written` 11-123 tracking demo-block size across
`n_examples`, one write at prefill, layer 14, `rescue_donor = clean`). **So the instrument is sound
and the question can finally be asked.**

**The question.** `demo_processing_only` masks demo→demo attention across layers 6-14, and the attack
dies. **Is the information it destroys carried in the demonstration positions' residual stream at the
top of that band?** If so, handing those activations back — captured from a clean forward at the same
positions — should bring the attack back.

**Arms (Llama, d10 bank, 160 rows each):**
* **`p7_rescue_L14`** — primary. Rescue at **layer 14**, the top of the knockout band, so every
  downstream layer reads the demo positions as the clean run left them.
* **`p7_rescue_L5`** — **specificity control**. Rescue at **layer 5, BELOW the band.** Clean
  activations are written in, and then layers 6-14 mask them again. **A rescue that "works" here is
  not restoring band-specific information — it is doing something nonspecific, and would invalidate
  the L14 reading.**
* Baselines already on disk: `p4bA` (clean) and `p4b_demo_processing_only` (knockout-only), same bank,
  same rows, same session.

**Outcomes, fixed now:**

| outcome | pattern | reading |
|---|---|---|
| **A — localised** | L14 ASR returns to within `MARGIN_VS_BASELINE = 0.0521` of clean, **and** L5 does not | The information the knockout destroys **is** in the demo-position residuals at the top of the band |
| **B — partial** | L14 recovers, but the gap to clean exceeds 0.0521 | Some of it is there; the rest is carried elsewhere. **Report the fraction, do not round it to "localised"** |
| **C — null** | L14 stays within 0.0521 of **knockout-only** | The demo-position residual at L14 is **not** what the knockout destroys — the damage travels by another route |
| **D — invalid** | L5 recovers as much as L14 | The patch is nonspecific; **no localisation claim from either arm** |

**⛔ Pre-committed constraints.**
* **Refusal is reported beside ASR, never instead of it.** C-12 established these are separable
  effects; a rescue could restore one and not the other, and **that dissociation is itself a result**.
* **`rescue_liveness.fired` must be true on every row of every arm**, or the arm is reported as
  UNMEASURED rather than null — R-32 is exactly why this is a stated precondition.
* **Truncation travels with every number** (DR-2: Llama is 58-73% capped at 192 tokens).
* **No layer sweep.** Two layers, chosen for a reason, fixed in advance. **Scanning layers until one
  "rescues" is how a floor becomes a search** — and with 160 rows and a 0.0521 margin (8.3 rows) a
  sweep would find something.
* **Llama only.** Cross-model comes only if Outcome A or B holds.

**Judging:** pinned `openai/gpt-4o-mini`, prefix `p7j`, joined by `completion_sha256_16` as always.

---

### ✅ R-33 (20:50) — **THE IDENTITY CONTROL PASSES, 8/8 BYTE-IDENTICAL. The rescue instrument writes exactly what it read. The gate that blocked every rescue number is now open.**

**Job 781047**, `--rescue-donor self`: capture the arm's activations **under the arm's own hooks**,
then write them straight back. **If the patch is sound this must reproduce the arm exactly.**

| comparison | identical rows |
|---|---|
| **identity control vs knockout-only** | **8 / 8** |
| identity control vs rescue (clean donor) | **0 / 8** |

**Per-row `n_chars` match exactly on all eight**, including the outlier `d3668c5c` at **119 / 119** —
the short-refusal row. **A misaligned or partial write could not reproduce a 119-character refusal
character-for-character.**

**What this rules out**, which is the whole reason the control exists:

* the patch writing to the **wrong positions** (would perturb 8/8),
* writing the **wrong dtype/device-cast** values (would perturb),
* firing on the **wrong forward pass** or the wrong layer (would perturb),
* **not firing at all** (would also give 8/8 — but then `rescue` vs `identity` would be 8/8 too, and
  it is **0/8**). **The two comparisons together are what make the result airtight: identical where it
  must be, different where it must be.**

**So the instrument is validated end-to-end on the real model**, complementing the fake-model unit
tests (write-correctness, locality, hook removal) and `strict_ids` (alignment). **R-31's flagged gap
is closed and R-32's gate is open.**

#### Where §20 Q3 now stands

The rescue **fires** and is **sound**. What it does is not yet measured: the 8-row smoke shows rescue
differing from both knockout-only and clean on 8/8, with one suggestive row (`d3668c5c`: 119 chars
knocked out → 760 rescued). **n=8, unjudged, and nothing is claimed.**

**Next, in order:** re-read the resubmitted smoke (`781168`) for the now-recorded `rescue_liveness`
field → **pre-register what a rescue would and would not demonstrate** → then the sweep at 160 rows
with judging. **No rescue number is read before that pre-registration exists.**

---

### R-32 (20:45) — **The rescue smoke ran and the patch FIRES — but the run could not PROVE it, because I built `DonorPatch.liveness()` and never recorded it. Fixed, tested, and the smoke resubmitted. Still no science.**

**Job 781006** (8 rows, Llama, `demo_processing_only` 6-14, rescue at layer 14): **COMPLETED**,
`failures: {}`, knockout liveness healthy (`min_decode_forwards = 1719`, `median_n_demo_positions =
36.5`). Run dir `outputs/boombness/score_behavior/p7smoke_rescue_L14_20260825_203342_868912`.

**Did the patch fire? Yes — but I had to infer it from generations, which is exactly the wrong way.**

| comparison | identical rows |
|---|---|
| rescue vs **knockout-only** | **0 / 8** |
| rescue vs **clean baseline** | **0 / 8** |

So the patch changed the computation and did **not** trivially restore the clean run. One row is
suggestive on its own: `d3668c5c` produced **119 chars under the knockout** (the short refusal
signature) and **760 chars under the rescue**. **n=8, unjudged, and nothing is claimed from it.**

#### 🔴 The defect: an instrument that cannot prove it fired

**I wrote `DonorPatch.liveness()` in R-30, and then never wired it into the artifact.** The run
completed cleanly, wrote 8 rows, reported no failures — **and contained no field that could
distinguish "the patch fired" from "the patch silently did nothing".**

**That is precisely the failure this phase's whole liveness discipline exists to prevent**, and it is
the third time in this sprint an instrument looked healthy and was not (C-6: the readout hook never
recorded; C-8: batch collision; DR-3: the cross-row donor capture). **A rescue that never fired
produces a null indistinguishable from "the information was not there" — the most dangerous null
available in this experiment.**

**Fixed:** every row now carries `rescue_liveness` (`n_positions_written`, `n_forward_calls`,
`fired`), plus `rescue_layer` and `rescue_donor`. **0 lines deleted.** A test asserts
`_rescue_ctx.liveness()` is called *and* that its value reaches the emitted row —
`test_rescue_liveness_is_recorded_on_the_row`. Suites: **57 passed**.

**Smoke resubmitted** under the fixed code, because a smoke whose only job is to prove the hook fires
must be run by the version that records it. **The earlier run is not deleted and is not used as
evidence.**

⚠ **Gate still closed.** The identity control (`781047`, `--rescue-donor self`) is **PENDING with an
estimated start of 2026-08-26** under fair-share. It has **not** been cancelled. **Until it passes —
writing a run's own activations back must reproduce it byte-identically — no rescue number will be
read, because a patch that does not write what it read makes every rescue result meaningless.**

---

### 🔎 DR-3 (20:20, 4h DEEP REVIEW) — **Suite 1368/0. Pool-B provenance verified and DISCRIMINATING. R-29 recomputed exactly. And I made a silent cross-row bug while closing R-31's gap, caught it with my own ordering check, and turned it into a test.**

**Suite:** `1368 passed, 7 skipped, 0 failed`, serial and exclusive; `git status outputs/ reports/
data/` clean before and after.

**Pool-B bank provenance (not covered by DR-2, which predated pool B):**

| arm | rows | not in bank B | sha mismatch | **also matches bank A** |
|---|---|---|---|---|
| all four `p6b*` | 160 each | **0** | **0** | **0** |

**`also_matches_bank_A = 0` is the part that matters** — it proves the check *discriminates*. A
provenance test that would pass against either bank tests nothing; this one would have caught a
bank mix-up.

**R-29 recomputed from raw rows, no helper shared with the original:** baseline `1/160 = 0.0063`;
`demoproc` **32/160 = 0.2000, rise +0.1938 ABOVE margin**; `legacy` 4/160 (+0.0188, within);
`respq` 2/160 (+0.0063, within). **Exact match.**

**Saturation / floor check on the headline.** Finest resolvable step is `1/160 = 0.00625`; the margin
is 8.3 rows. The three C1 rises are **26, 21 and 31 rows** — **2.5-3.7× the margin, nowhere near the
floor, and nowhere near saturation** (the largest arm rate is 0.2000, far from 1.0). **No structure is
being fitted below the measurement floor.**

**Pool-B truncation** matches pool A's pattern (baseline 91/160 at cap, `demoproc` 114/160),
consistent with DR-2 and already carried as a stated limitation.

#### 🔴 A bug I made this tick, caught by my own check

Closing R-31's flagged gap meant adding `--rescue-donor self` — the classical identity control, where
a run's own activations are written back into it and **must reproduce it exactly**. My first
implementation captured the donor **before** `ctxs = make_intervention(...)` existed.

**Python would not have raised.** `ctxs` is function-scoped and still bound from the **previous loop
iteration**, so under `--rescue-donor self` the donor would have been captured **under the previous
ROW's hooks** — silently, plausibly, and wrong. **It is the absolute-position-index bug class wearing
a different costume: state from one example reused on another.**

Caught by grepping the line numbers of the build site and the capture site rather than by trusting the
patch. **Fixed** by moving the capture to after `ctxs` exists, and **converted into a static
regression test** (`test_donor_capture_happens_after_ctxs_is_built`) because the failure is one of
**source order**, not of behaviour on any single row — no row-level test would have caught it.

Two further guards added: every rescue statement is asserted to live under
`if args.rescue_layer is not None:`, and the identity-control option is asserted to exist at all.
**`test_donor_patch.py` 13/13; the four knockout suites 137/137.**

**Still zero science.** Both smokes (`781006` rescue, and the identity control submitted this tick) are
**queued behind fair-share**; `781006` has been PENDING on Priority since 19:40 and **has not been
cancelled**, per the standing instruction.

---

### R-31 (19:45) — **The rescue is wired into `score_behavior` ADDITIVELY, and the inertness is PROVEN by diff rather than asserted. Smoke job 781006 submitted; nothing read yet.**

**The integration.** `--rescue-layer L` (default `None`). When set, before the intervention context is
entered, a **clean forward over the same `templated_r`** captures `resid_post` at layer L over the
demo-block positions `dk`; the resulting `DonorBlock` is applied as one more context manager appended
to the existing `ExitStack`. **Every existing path — `resolve_occurrences`, `demo_key_positions`,
`make_intervention`, liveness, judging, provenance — is reused unchanged.**

**Why donor and recipient cannot drift:** both use **the same `templated_r` and the same `ids_r`**, and
`dk` is computed **once** and passed to both. Positions are identical by construction — **and
`DonorPatch` re-verifies token identity over the span anyway**, because "identical by construction" is
what both prior absolute-index defects in this repo also believed.

**Inertness, proven not claimed:**

| check | result |
|---|---|
| lines **deleted** from `score_behavior.py` | **0** |
| lines added | 31 |
| added lines outside a rescue guard or the new flag's help text | **0** (all 12 unfiltered ones are help-string continuations or bodies of `if args.rescue_layer is not None:`) |
| behaviour without `--rescue-layer` | **unchanged by construction** — the only new statements are inside that guard |
| affected suites | `test_scoped_knockout_wiring`, `test_readout_liveness`, `test_nondemo_control_draws`, `test_donor_patch`, `test_metric_names` — **147 passed** |

**Two refusals built in, both charged to the ledger rather than silently skipped:**
* `rescue:no_knockout_or_no_demo_keys` — **rescuing a run that was never knocked out is a no-op dressed
  as an experiment.**
* `rescue:donor_capture_empty` — a donor that captured nothing must not proceed as if it had.

**Smoke (job 781006):** 8 rows, Llama, `demo_processing_only`, band 6-14, **rescue at layer 14** — the
top of the knockout band, so downstream layers read demo positions as the clean run left them.
**PENDING at tick close under fair-share; no number is read until it lands.**

**⛔ Still not claimed.** No rescue result exists. The smoke's job is only to show the patch **fires**
(`DonorPatch.liveness()['fired']`) and that generations **change** versus knockout-only. **A
pre-registration fixing what a rescue would and would not demonstrate comes before any sweep.**

⚠ **Deferred instrument check, recorded so it is not forgotten:** the classical α=0 identity control
(patch a run's own activations into itself → must reproduce it byte-identically) is **blocked by my own
`no_knockout` refusal**. Unit tests cover write-correctness and locality on a fake model, and
`strict_ids` covers alignment on the real one, but **the end-to-end identity control has not been run**
and that is a gap in the instrument's validation, not a gap in the science yet.

---

### R-30 (19:15) — **§20 Q3 restarted. The rescue primitive is built and mutation-verified; NO science is claimed yet. Also: why `LayerPatch` could not be reused, and why the alignment guard is the whole design.**

**Decision first (step 2 of the cadence).** Of the three unrun §20 questions, current evidence
justifies **only Q3**. **Q6** (joint crossed Qwen3 factorization) is **dropped**: its motivating
hypothesis, `d_surface` as an objective, is closed, and the cross-model representation question it
targets is already answered by R-17's Qwen3 within-family bridge. **Q4** is gated on Q3 and stays
gated. **Q3 survives because it is the only route to the one thing this phase measured and did not
explain** — what carries the coherent non-compliance in R-21.

**Why existing code could not be reused.** `ds_common.LayerPatch` writes **one vector, shaped
`[hidden]`, to every requested position**. A rescue asks a different question — *give the knocked-out
run back exactly the activations the clean run had at each demonstration position* — which needs a
**`[n_positions, hidden]`** donor block. `patched_generate` likewise only stacks `LayerPatch` tuples
and cannot compose with a knockout context manager. **So this is a genuine build, not a re-cut, and it
is reported as such.** `src/boombness/donor_patch.py` is a **sibling** of `LayerPatch`; nothing
existing was edited.

**⛔ The bug class this file was written against.** Donor and recipient are **two different forward
passes**. This repo has twice shipped a defect where a position computed on one example is reused as
an absolute index on another, and a donor patch is the ideal host for it: **if the two tokenisations
differ by one token, the patch writes the right activations to the wrong places and still returns a
plausible number — a null that looks like evidence the information was not there.**

Three guards, all mutation-verified rather than asserted:

| mutation | result |
|---|---|
| misaligned recipient, `strict_ids` **ON** | **REFUSED** — guard is load-bearing |
| same misalignment, `strict_ids` **OFF** | **wrote 2 positions** — so the guard is the *only* thing preventing a silently misaligned rescue |
| donor positions past the sequence end | `liveness() = {'n_positions_written': 0, 'fired': False}` — a rescue that never fired **reports** it rather than being inferred to have worked |

`DonorBlock` additionally refuses row/position count mismatches, non-2-D activations, and **duplicate
positions** (two rows targeting one position makes the written value depend on write order).

**Tests:** `tests/test_donor_patch.py`, **10/10 pass** — locality (positions 0 and 3 untouched),
hook removal on `__exit__`, the short-recipient refusal, and the no-`input_ids` refusal.

**⛔ Explicitly NOT claimed.** No rescue has been run. No model has been loaded. **This tick delivers a
verified instrument and nothing else**, which is the correct order for a causal experiment in a hot
path — the phase's own C-6 and C-8 were both instruments that looked fine and were not.

**Next:** capture donor activations from the clean run at the knockout's own band (6-14 on Llama),
apply them under `demo_processing_only`, and ask whether the attack returns — **pre-registered before
any arm is submitted, and smoked before any sweep.**

---

### 🏆🏆🏆 R-29 (18:35) — **PR-12 PASSES BOTH CONDITIONS. C1 replicates on a demonstration pool that shares NO sentences with the original. The refusal-restoration result now stands in three independent settings.**

**Artifacts:** arms `p6b*` (jobs 780892-780895), judging `p6bj_*` (job **780928**), bank
`boombness_prompt_bank_d10_poolB.jsonl` (`b3e256a0fd0cc296`).
**Provenance:** `openai/gpt-4o-mini` on **640/640** rows; `completion_sha256_16` joins **640/640**.
All arms `frac_rows_scope_live = 1.0`, `scope_violations = {}`.
**PR-12 was committed at `abbfb621`, before pool B existed.**

**Pool B baseline: ASR 0.1688, keyword-refusal 0.0063** — read from pool B's own baseline arm, as
pre-registered, and **notably lower than pool A's 0.0563**, which is exactly why the rule said not to
assume it.

| arm | ΔASR | refusal | **rise vs pool-B baseline** | vs 0.0521 | killed | by refusal |
|---|---|---|---|---|---|---|
| **`demo_processing_only`** | −0.1313 | **0.2000** | **+0.1938** | **ABOVE** | 24 | **9 (38%)** |
| `legacy_all_query` | −0.1375 | 0.0250 | +0.0188 | within | 26 | 1 (4%) |
| `response_query_only` | −0.1187 | 0.0125 | +0.0063 | within | 23 | 1 (4%) |

**Condition 1 — HOLDS.** `demoproc` rise **+0.1938**, **3.7× the margin**, and the **largest of the
three settings measured** (Llama pool A +0.1625, Qwen3 pool A +0.1312).
**Condition 2 — HOLDS.** legacy **+0.0188** and respq **+0.0063**, both well inside margin.
✅ **C1 REPLICATES on an independent demonstration pool.**

#### What C1 now rests on

| setting | model | pool | baseline refusal | `demoproc` rise | others |
|---|---|---|---|---|---|
| 1 | Llama-3.1-8B | A | 0.0563 | **+0.1625** | all within margin |
| 2 | Qwen3-14B | A | 0.0125 | **+0.1312** | all within margin |
| 3 | **Llama-3.1-8B** | **B** | **0.0063** | **+0.1938** | all within margin |

**Two model families and two demonstration pools sharing no sentences.** Across all three, the same
single scope of four restores refusal and no other does. **§20 Q5 is answered: the mechanism survives
an independent demonstration pool.**

#### ⚠ Honest annotations

* **`legacy` and `respq` are no longer at exactly zero** — 1 killed-by-refusal each (4%), against 0/0
  in both pool-A settings. **Both are still inside the margin and the contrast with demoproc's 38% is
  unchanged**, but "exactly zero in every cell" is no longer accurate and should not be written.
* **Pool B's baseline refusal is 0.0063 (1 row of 160)** — nearly a floor. A rise measured against a
  near-zero baseline is easier to clear, which is a reason to weight setting 1 (baseline 0.0563) most
  heavily, not least.
* **ASR magnitudes are NOT part of this replication** — PR-12 pre-committed that. Descriptively they
  again cluster (−0.1313 / −0.1375 / −0.1187, all pairwise gaps ≤ 0.0188 < 0.0417), which is
  **consistent with C3 but is not a pre-registered test of it here** and is recorded as description
  only.
* **`query_prefill_only` was not run** on pool B — it appears in neither PR-12 condition. C8 remains a
  single-pool result.

---

### R-28 (18:00) — **PR-12's three pre-arm gates ALL PASS. Pool B is genuinely independent — 0 of 40 pools share a sentence set with pool A — and the confirmatory arms are submitted.**

**Pool B:** `data/boombness_prompts/demo_pools_d10_poolB.json` (job **780821**, seed `20260825`).
**Bank B:** `data/boombness_prompts/boombness_prompt_bank_d10_poolB.jsonl`.

| gate | check | result |
|---|---|---|
| **3 (run first)** | pools with identical sentence sets, by **sha256 of the sentence list** | **0 / 40** — all 40 differ |
| **1** | `prompt_families.py --strict` | `families checked=560 violations=0`, `duplicates dropped=0`, exit 0 |
| **2** | `tokenization_audit.py` (job **780879**) | `rows ok=4560 bad=0 ambiguous=0`, **`token-alignment violations=0`** |
| — | bank identity | A `368566acecdc350f` vs B **`b3e256a0fd0cc296`** — differ |

**Gate 3 was run FIRST and deliberately so.** A seed that silently produced the same sentences would
have made this a re-run of R-19 under a new filename, and every downstream number would have looked
like a replication while being the same data. **Checking sentence-set hashes rather than file paths is
the difference between testing independence and assuming it.** `ambiguous=0` on pool B against
`ambiguous=7` on pool A is incidental, not a quality signal, and nothing is read from it.

**Submitted (Llama, jobs 780892-780895):** `p6bA` baseline, `p6b_demo_processing_only`,
`p6b_legacy_all_query`, `p6b_response_query_only` — the baseline plus exactly the three arms PR-12's
two conditions require. `query_prefill_only` is **not** run: PR-12 tests C1, and `qpre` appears in
neither condition. Argsfiles are committed under `runargs/p6/` and were **grepped back** to confirm no
bank-A path leaked through the substitution.

**No result is read until all four land.** PR-12's conditions, its pool-B-baseline rule, and its list
of what does **not** count were fixed at commit `abbfb621`, before the pool existed.

---

### PR-12 (17:40) — **Pre-registered: §20 Q5's fourth independent demonstration pool, run as a CONFIRMATORY test of C1 on entirely new demonstration sentences.**

**This is the gap the handoff refused to call "superseded".** Both a fourth pool and more domains were
requested; only the domain expansion (R-18) was delivered. **This closes it.**

**What "independent pool" means here, stated precisely.** Same concept/codeword (`bomb`/`carrot`), same
10 domains, same design, same generator (GPT-4o-mini via `prepare_demos.gen_demos`) — **a different
generator seed, hence entirely different demonstration SENTENCES.** That is the axis §20 Q5 asks
about: the mechanism must not depend on the particular demo text the pool happened to contain.
Job **780821**, seed `20260825` against the incumbent `20260816`.

**One code change, additive.** `run_demo_pools.sh` hardcoded `--seed 20260816`; it now reads `DP_SEED`
**defaulting to that same value**, so every prior invocation reproduces byte-for-byte. No other file
is touched.

**⛔ This is CONFIRMATORY, and the claim under test is fixed before the pool exists.** The claim is
**C1**, the phase's strongest result:

> `demo_processing_only` restores refusal; the other scopes do not.

**Replication requires BOTH:**
1. `demo_processing_only`'s keyword-refusal rate exceeds the **pool-B baseline's** by more than
   `MARGIN_VS_BASELINE = 0.0521`.
2. `legacy_all_query` and `response_query_only` each stay **within** 0.0521 of that baseline.

**Refuted if** either fails. **The pool-B baseline is read from pool B's own baseline arm and is not
assumed equal to** the d10 baseline (0.0563 Llama).

**⛔ Pre-committed as NOT counting**, consistent with PR-6 and C-11:
* **ASR magnitudes and any ranking of arms.** C-11 established these sit inside the margin; a different
  ordering on pool B is not evidence of anything.
* **The domain sign test's p or floor.** Baseline ASR will differ, so attainable evidence differs.
* **Refusal dose-response.** That is C6, single-model and separately refuted on Qwen3 (R-22); pool B is
  not being used to relitigate it.

**Model: Llama only**, as §20 Q5 specifies ("especially on Llama"), and because C1's Llama refusal rise
(+0.1625) is the larger of the two and therefore the more falsifiable target.

**Gates before any arm is submitted**, in order, each of which can stop this branch:
`prompt_families.py --strict` (0 violations) → `tokenization_audit.py` (0 alignment violations) →
**pool B must differ from pool A** (a seed that silently produced identical sentences would make this
a re-run of R-19 wearing a new name, and I will check the sentence-set hashes, not the file names).

---

### ⛔ R-27 (16:45) — **PR-11 IS UNINFORMATIVE, and I am reporting it as such rather than as the headline it briefly looked like. Concept-term usage is CONFOUNDED WITH THE OUTCOME: in this bank the concept terms ARE the harmful content.**

**What it looked like at first.** Among killed attacks, concept-term usage **collapses**:

| | baseline **jailbroken** | `demoproc` killed | `legacy` killed | `respq` killed |
|---|---|---|---|---|
| **Llama** | **64%** (16/25) | **0%** (0/25) | **0%** (0/24) | 4% (1/24) |
| **Qwen3** | **81%** (17/21) | **0%** (0/20) | 11% (2/19) | 5% (1/20) |

Read naively that says *the model stops using the mapping when the attack dies* — which would
**contradict R-16/R-17**, where the binding survived the same intervention. PR-11 pre-flagged that a
disagreement between the probe and free generation would be a real result. **It is not one. The
comparison is broken.**

#### The check that killed it

PR-11's own confound clause required the baseline's own rate. **The correct comparison is not
baseline-jailbroken but baseline-NOT-jailbroken** — rows where no intervention was applied and the
attack simply did not land:

| | baseline NOT jailbroken | **killed rows (all arms)** |
|---|---|---|
| **Llama** | **6%** (8/135) | **0-4%** |
| **Qwen3** | **10%** (14/139) | **0-11%** |

**Killed rows look exactly like untreated rows that were never jailbroken.** The concept-usage drop is
**entirely explained by jailbreak status**, which is true in the baseline with no intervention at all.

> **In this bank, "mentions bomb/explosive/detonate" and "is a successful jailbreak" are close to the
> same event.** StrongREJECT scores a row ≥ 0.5 largely *because* it produced that content. **So
> "killed rows contain less concept language" is very nearly a restatement of "killed rows scored
> lower" — a measure confounded with the outcome it is being used to explain.**

#### The verdict

**PR-11 is answered NO — it cannot be answered with this instrument.** The lexical concept flag cannot
separate *"the mapping stopped being used"* from *"the harmful content is absent"*, because in this
bank they are the same tokens. **No claim about mapping usage in free generation is made, and R-16 /
R-17 are neither supported nor contradicted by it.**

**What I nearly published.** A 64% → 0% collapse across two models, with a ready-made story about
representation and use. **The tautology check was in PR-11 as a pre-committed confound clause, and
running it is the only reason this is a null instead of a headline.** Recorded here as an instrument
failure, in the same register as a result.

**A version that WOULD work, recorded rather than attempted:** the flag would have to be a concept
term that is **not** itself harmful content — the mapping expressed in a benign register. That is a
bank-design requirement (a codeword whose concept has neutral vocabulary), joining R-25's
longer-context requirement on the list of things this bank cannot answer. **Not attempted now.**

⚠ Also observed, too thin to interpret: the still-jailbroken cells hold **n = 0, 1, 2** rows — these
arms killed nearly every attack they touched, so there is no surviving-attack population to compare
against.

---

### PR-11 (16:40) — **Pre-registered: when the attack dies, does the MAPPING stop being used? And a pre-commitment NOT to use the 5-way phenotype cascade on this data.**

C-12 left the phase with an effect and no mechanism. R-16/R-17 showed the mapping **survives** in a
forced-choice probe; this asks the complementary behavioural question: **in the completions where the
attack was killed, does the model still talk about the CONCEPT, or has it fallen back to the
CODEWORD's literal meaning?**

**⛔ First, an instrument I am refusing to use.** `completion_phenotype.lexical_phenotype` is an
ordered cascade in which `truncated` is tested **before** concept terms, so any row ending on
`stop_reason == "length"` becomes category 4 (`garbled_or_nonanswer`) regardless of content. **DR-2
measured 58-73% truncation on Llama.** The 5-way distribution would therefore be **dominated by the
cap, not by the intervention**, and its category-4 mass would be an artifact of `--max-new 192`.
**The cascade is not used here, and no 5-way phenotype number will be quoted for this phase.** (Its
own docstring already forbids it as a primary estimator until reliability is measured; truncation is a
second, independent reason.)

**What IS used:** the two **truncation-independent booleans** from the same module,
`has_codeword` and `n_concept_terms_hit` — deterministic substring tests, no API, no session drift,
unaffected by where the completion stops.

**The question, on KILLED attacks only** (baseline jailbroken, arm not):

* **`concept_used`** — completion contains a concept term.
* **`codeword_only`** — contains the codeword and no concept term.

**Prediction if killing the attack works by breaking the mapping:** killed rows should be
**`codeword_only`** — the model reads `carrot` as a carrot. **This would CONTRADICT R-16/R-17**, which
found the binding intact, and I flag that in advance: **the two instruments measure different things
(forced-choice probe vs free generation) and a disagreement is a real result, not an error to
reconcile away.**

**Prediction if the mapping is intact and only the compliance changed:** killed rows still reference
the concept at rates comparable to the baseline's jailbroken rows — **the model knows what `carrot`
means and declines to help anyway.**

**⛔ Confound stated first.** The prompt itself contains the codeword, so any completion that echoes
the question scores `has_codeword` **without that meaning anything about the mapping**. Therefore
**`codeword_only` is only interpretable against the baseline's own rate**, never in absolute terms,
and the baseline rate is reported in every table. **Concept-term presence carries the inference; the
codeword flag is context for it.**

Zero new compute. Both models. Killed-row counts are 15-25 per cell (R-21), so this is **descriptive
with small denominators and will be labelled as such.**

---

### 🔎 DR-2 (16:10, 4h DEEP REVIEW) — **Full suite 1358/0. Provenance verified at CONTENT level on all 13 arms. One real exposure found: on Llama, 93/160 baseline rows hit the 192-token cap, and the untruncated subgroup is too small to test the effect. Qwen3 is barely truncated and the effect holds there cleanly.**

**Suite:** `1358 passed, 7 skipped, 0 failed` (299 s, serial and exclusive per C-2). `git status
outputs/ reports/ data/` clean before and after — **no repeat of C-2's artifact corruption.**

**Provenance, checked by CONTENT and not by filename.** My first sweep read `summary.json['args']`,
found `None`, and reported the bank as unknown on all 13 arms — **that was my check being wrong, not a
provenance gap**; the bank path lives in `config.json` / `RUNMETA.json` / `metadata.json`. Redone
properly by joining every result row's `prompt_sha16` against **both** banks, so a row from the wrong
bank would be detectable:

| check | result |
|---|---|
| arms verified | **13/13** (5 Llama, 5 Qwen3, 3 capped controls) |
| rows not present in the d10 bank | **0** |
| `prompt_sha16` mismatches | **0** |
| d10 bank sha256[:16] | `368566acecdc350f` — **matches C-10's recorded value** |
| duplicate judge tags (silent-overwrite hunt) | **0** across `p4bj`, `q4bj`, `p5j` |
| models | Llama-3.1-8B-Instruct ×8, Qwen3-14B ×5 — **no cross-contamination** |

#### ⚠ The exposure: every ASR in this phase is the ASR of the first 192 tokens

| arm | rows at the 192-token cap |
|---|---|
| **Llama baseline** | **93/160 (58%)** |
| Llama `demo_processing_only` | **116/160 (73%)** |
| Qwen3 baseline | 42/160 (26%) |
| Qwen3 `demo_processing_only` | 99/160 (62%) |

**A majority of Llama baseline completions never finished.** StrongREJECT is therefore scoring a
truncated answer on most rows, and `demo_processing_only` truncates *more* than baseline on both
models — a mechanism by which an ASR could fall without the model refusing anything.

**Diagnostic (⚠ conditions on `stop_reason`, which is POST-TREATMENT — a collider. This cannot settle
causality and is not offered as an estimator):** restricting to rows where **both** baseline and arm
ended on EOS:

| model | arm | full ΔASR | both-EOS n | baseline attacks there | both-EOS ΔASR |
|---|---|---|---|---|---|
| **Qwen3** | `demoproc` | −0.0875 | **51** | 7 | **−0.1176** |
| **Qwen3** | `legacy` | −0.1062 | **111** | 13 | **−0.0901** |
| **Qwen3** | `respq` | −0.1125 | **114** | 14 | **−0.1053** |
| Llama | `demoproc` | −0.1500 | 22 | **3** | −0.1364 |
| Llama | `legacy` | −0.1250 | 26 | **0** | **+0.0000 — undefined** |
| Llama | `respq` | −0.1062 | 45 | 7 | −0.0667 |

**On Qwen3 the untruncated subgroup is large (111 and 114 rows) and every effect survives at
essentially full size.** That is the reassuring half, and it is the half that matters for the
cross-model claims: **the model with only 26% truncation reproduces the effects.**

**On Llama it cannot be tested.** The both-EOS subsets hold 3, **0** and 7 baseline attacks.
**`legacy`'s `+0.0000` is not evidence of no effect — there were no attacks in that subset to remove**,
and reporting it as a null would be exactly the empty-denominator error `coherence_gate`'s header
warns about in another guise.

**Ledger consequence, recorded rather than argued away:** every Llama ASR in R-19, R-22, R-23 and R-26
is **an ASR over 192-token completions with 58-73% truncation**, and its truncation-robustness is
**untestable on that model with this cap**. **The cross-model results are what carry the phase**, and
they carry it from the *less* truncated model. **No number is retracted; the scope of "ASR" is now
stated.**

**Not fixed by re-running at a larger cap**, and I am not launching that: it would change the measured
quantity, so old and new arms would not be comparable, and the phase's conclusions are cross-model
ones that already rest on the clean side. **Recorded as a bank/config limitation alongside R-25's.**

---

### R-26 (15:50) — **The capped control: UNINFORMATIVE where under-matched, as PR-10 said it would be — but at `n_examples = 2` it happens to be 0.989-matched, and there `demo_processing_only` separates from it cleanly. Demonstration-specificity gets ONE powered, matched dose. Not more.**

**Artifacts:** arms `p5_capped_d{1,2,3}` (jobs 780300-780302), judging `p5j_capped_d*` (job **780390**).
**Provenance:** `openai/gpt-4o-mini` on **480/480** rows, completion-hash joins **480/480**.
**Draws verified independent** — seeds 28180602 / 36100379 / 44020156, and the three arms produce
different generations on ~37% of rows (identical on 101, 106 and 100 of 160 pairwise), so d1/d3
sharing a total edit count is a count coincidence, not a seed collision. All three:
`frac_rows_scope_live = 1.0`, `scope_violations = {}`, `total_decode_edits = 0`.

**ΔASR against the same `p4bj_A` baseline, per dose, with the capped arm's own match ratio:**

| dose | attacks | `demoproc` | cap d1 | cap d2 | cap d3 | **cap mean** | **match ratio** |
|---|---|---|---|---|---|---|---|
| 1 | 2/40 | −0.0500 | +0.0500 | +0.1500 | +0.0000 | **+0.0667** | **1.000** |
| **2** | **5/40** | **−0.1250** | −0.0250 | +0.0000 | −0.0250 | **−0.0167** | **0.989** |
| 4 | 8/40 | −0.1750 | −0.1500 | −0.1250 | −0.0750 | −0.1167 | 0.547 |
| 8 | 10/40 | −0.2500 | −0.1000 | −0.1000 | −0.0250 | −0.0750 | 0.272 |

**Overall: capped mean ΔASR −0.0354, INSIDE the 0.0521 margin**, against `demoproc`'s −0.1500.
**Per PR-10 that overall null is UNINFORMATIVE and is not being quoted as support** — the capped arm
masks 27-55% as many positions at the high doses, and under-masking trivially predicts no effect.

#### The one cell that is both matched and powered

**At `n_examples = 2` the capped draw is 0.989-matched** (mean; min 0.857, only **5 of 40 rows** below
1.0). That is close enough to call a matched control, and PR-9's own power rule admits the dose —
baseline **5 attacks in 40 rows = 0.125 ≥ 0.10**.

> **`demo_processing_only` removed 5 of the 5 attacks. The count-matched non-demo control removed
> 0.67 of 5 on average** (1, 0, 1 across three independent draws). **Gap 0.1083, clearing the 0.0417
> arm-vs-arm margin by 2.6x.**

**That is the demonstration-specificity comparison R-25 said could not be built — and it exists at
exactly one dose, by accident of the capped policy rather than by design.** Masking the same number
of positions somewhere else does **not** reproduce the effect there.

#### ⛔ What this does NOT do

* **It does not overturn R-25.** At `n = 4` (ratio 0.547) and `n = 8` (ratio 0.272) the control is
  under-matched and its partial effect is **exactly what under-masking predicts**, so those doses stay
  **UNTESTED**. The effect is largest there, and that is where the comparison is still missing.
* **It does not rest on the `n = 1` cell**, which is fully matched (1.000) but has **2 attacks** and
  shows the control moving the *wrong* way (+0.0667). **R-9 declined that cell in advance and it stays
  declined** — I am not quoting a +0.0667 as anything.
* **It is one dose, 5 attacks, one model.** A gap of 0.1083 built on 5 attacks is **suggestive, not
  established.** The honest summary is: *the only powered matched comparison available favours
  demonstration-specificity, and there is exactly one of them.*

**No follow-up is launched to manufacture more matched doses.** Doing so requires the longer-context
bank recorded in R-25, which is a bank-design change. **The phase's stated limitation stands, now with
one supporting data point rather than none.**

⚠ Capped refusal rates are 0.0500 / 0.0375 / 0.0375 against a 0.0563 baseline — **all three at or
below baseline**, consistent with R-19/R-21: only `demo_processing_only` restores refusal, and
non-demo masking does not.

---

### ⛔ R-25 (15:08) — **GATE FAILED, BRANCH STOPPED. The strict count-matched non-demo control is feasible at ONE dose, and it is the dose with 2 attacks in 40 rows. Demonstration-specificity CANNOT be tested by this control on this bank.**

**Jobs 780297-780299 (all three strict draws): FAILED, refusing before generating.** My PR-10 smoke
saw only 8 rows from a single domain (`warehouse_logistics`) and reported n=1 and n=2 both feasible.
**On the full 10-domain population that is false:**

| n_examples | rows OK | rows infeasible | `match_ratio` min / mean |
|---|---|---|---|
| **1** | **40/40** | 0 | **1.0 / 1.0** |
| **2** | 35/40 | **5** | **0.0 / 0.875** |
| 4 | — | all | 0.0 / 0.0 (R-24) |
| 8 | — | all | 0.0 / 0.0 (R-24) |

**⛔ And the obvious workaround is explicitly forbidden by the module itself.** Its refusal message:

> *"Fix the arm or the population — do NOT rescope to the feasible rows, because demo length IS the
> dose variable and dropping the long-demo rows silently changes the experiment."*

**That is correct and I am obeying it.** Keeping the 35 feasible rows at `n = 2` would select on demo
length *within* a dose level — the shorter demo blocks are exactly the feasible ones — manufacturing a
control population that differs from the arm population on the variable under study.

**So the strict control is feasible only at `n_examples = 1`, in full.** And `n = 1` is the cell
**R-23 already declined as underpowered**: Llama baseline there is **2 attacks in 40 rows**. A
count-matched control at that dose could distinguish nothing; both arm and control are inside the
margin by construction.

#### The branch is stopped, not rescued

Per the standing instruction — *"if a gate fails, say so and stop that branch of the plan rather than
rescuing it"* — **I am not running the `n = 1` strict control to have a number.** It would be a cell
that cannot discriminate, published next to a question it cannot answer.

**The finding is the infeasibility itself, and it is a real constraint on the paper:**

> **On this bank, a count-matched non-demonstration attention control cannot be constructed at any
> dose where the effect is measurable.** The demonstration block grows 12 → 106 tokens while the
> unprotected non-demonstration pool is near-constant at ~53, most of which is the query span a
> control must not touch. **By construction, there is nothing left to match against.**

**Consequence for every claim in this phase:** the scoped-knockout results establish *where* in the
sequence masking matters (demo span vs query prefill vs response), because those scopes are all
matched to each other. **They do NOT establish that masking the demonstrations specifically differs
from masking an equal amount of anything else — and on this bank that comparison is not
constructible.** This is now a stated limitation, not an open to-do.

**What still runs:** the three `capped` draws (780300-780302, all four doses), under PR-10's
**one-sided** rule — informative only if they *do* remove attack. **A null from them will not be
reported as support for demonstration-specificity.**

**Design note for any future bank.** The control is not impossible in principle, it is impossible
*here*: it needs a bank whose non-demonstration context is long enough to match a 106-token demo block
without touching the query — e.g. a neutral filler passage sized to the largest `n_examples`. **That
is a bank-design change, not an analysis change**, and it is recorded as such rather than attempted
now.

---

### R-24 (14:52) — **PR-10's smoke: the count-matched non-demo control is INFEASIBLE at exactly the doses where the effect lives. Reported as a limit, not routed around.**

**Job 780231** (8 rows, Llama, d10). **State: FAILED — and that is the correct outcome.** The module
**refused before generating** rather than emitting an under-matched control:

```
REFUSING before generating: 4 of 8 rows cannot carry this knockout
(0 without a demo block, 4 whose control cannot be built, 0 with no query rows)
```

**`control_draw_match_ratio`, per dose** (drawn keys / demo keys):

| n_examples | min | mean | rows below 1.0 | feasible? |
|---|---|---|---|---|
| 1 | **1.0** | 1.0 | 0 | **YES** |
| 2 | **1.0** | 1.0 | 0 | **YES** |
| **4** | **0.0** | 0.0 | 2 | **NO** |
| **8** | **0.0** | 0.0 | 2 | **NO** |

**Ratio 0.0 means not one position could be drawn.** The demo block grows 12 → 106 tokens while the
unprotected non-demo pool is near-constant (~53 tokens, mostly the protected query span), so by
`n_examples = 4` there is **nothing left to count-match with**.

**⛔ This is the pre-committed bad case.** PR-10: *"If the control is infeasible precisely where the
effect lives (n_examples 4 and 8), I will say the control cannot be run there and the
demonstration-specificity claim is UNTESTED at those doses."* **The effect lives there** —
`demo_processing_only`'s ΔASR is −0.1750 at n=4 and −0.2500 at n=8, against −0.0500 at n=1 (a 2-row
cell R-23 already declined as underpowered). **So the strict control can only speak where the effect
is weakest or unmeasurable.**

**What is being run, and the inference rule fixed in advance for each:**

* **`p5_matched_d1/d2/d3` (jobs 780297-780299)** — strict, count-matched, restricted to
  `n_examples ∈ {1, 2}` where `match_ratio = 1.0`. **80 rows.** These are a fair test **at low dose
  only.**
* **`p5_capped_d1/d2/d3` (jobs 780300-780302)** — capped, all four doses, **named `capped` and never
  reported as `matched`**, with `control_draw_match_ratio` quoted per dose. **The capped arm is
  ONE-SIDED and will be read only in the direction it can support:** it masks **fewer** positions than
  the arm, so **if it still removes the attack, that is evidence the effect is not
  demonstration-specific**; **if it does not, that is uninformative**, because under-masking trivially
  predicts no effect. **A null from the capped arm will not be quoted as support for
  demonstration-specificity.**

**Nothing here is a rescue of the strict control.** At `n_examples` 4 and 8, **demonstration-
specificity remains UNTESTED**, and that will be stated in the phase's conclusions rather than
softened by the low-dose cells.

---

### PR-10 (14:40) — **Pre-registered: the control C-12 makes unavoidable. Is ANY of this about DEMONSTRATIONS, or does masking an equal number of ARBITRARY positions remove the attack just as well?**

C-12 removed the mechanism this phase thought it had. What remains is: *four attention-masking scopes
all remove attack by coherent non-compliance, and one additionally restores refusal.* **Nothing in
that sentence yet establishes that the DEMONSTRATIONS are what matters.** If masking a count-matched
set of **non-demonstration** positions removes the attack just as well, then the whole scoped-knockout
result is about **removing attention mass**, not about demonstration retrieval — and the phase's
headline collapses to a much weaker claim.

**This control has never been run behaviourally.** `score_behavior` has carried
`nondemo_matched_d1..d3` and `nondemo_capped_d1..d3` since review finding M1 (2026-08-23), but every
historical invocation was a `semantic_one_word` readout (`g3wa_block`, jobs 766664-766672). **The code
exists and has never been pointed at the behavioural population.**

**Design, matched on everything that could otherwise explain a difference.** Identical bank (d10),
identical arm population, identical layer band 6-14, identical `--knockout-scope
demo_processing_only` — so the **query rows are the same demo-span rows**, and only the **KEY SET**
changes: `demo_all` masks the demonstration positions, `nondemo_matched_d*` masks **the same NUMBER**
of positions drawn from elsewhere. **Three independent draws (d1, d2, d3)**, because a single draw
that happens to hit nothing is a lucky draw, not a control.

**Prediction if the effect is demonstration-specific:** the non-demo control's ΔASR is **within
`MARGIN_VS_BASELINE = 0.0521` of zero**, against `demo_processing_only`'s **−0.1500**.

**Prediction if the effect is about attention mass:** the control's ΔASR is comparable to `demoproc`'s
— gap within the arm-vs-arm margin **0.0417**. **In that case the scoped-knockout finding is not about
demonstrations and every "demonstration processing" claim in this phase must be renamed.**

**⛔ The known failure mode, and why a smoke runs first.** `query_span_positions`' own docstring
records that the naive version of this control blocked **~98% of post-demo tokens at n_examples = 4** —
it was deleting the question being asked, with a dose that scaled with the arm's own dose, and the
docstring notes *"'random control ≥ demo knockout, therefore the effect is not demonstration-specific'
is a conclusion this project has already retracted once."* The strict policy protects the query span,
which means **the draw pool may be too small to count-match at high `n_examples`** (the demo block
grows 12 → 106 tokens while the unprotected non-demo pool is near-constant). **Job 780231 is an
8-row smoke whose only purpose is to read the pre-flight's `infeasible_control` count per
`n_examples` before any sweep is submitted.**

**Pre-committed handling of infeasibility:** if strict count-matching is infeasible at some doses, the
control is reported **only at the doses where it is feasible**, with `control_draw_match_ratio` quoted
on every row. **A `capped` draw will NOT be silently substituted for a `matched` one** — the module
enforces separate arm names for exactly this reason, and an under-matched control that "shows no
effect" would be an artifact of under-matching. **If the control is infeasible precisely where the
effect lives (`n_examples` 4 and 8), I will say the control cannot be run there and the
demonstration-specificity claim is UNTESTED at those doses, rather than quoting the low-dose cells as
if they settled it.**

---

### 🔴🔴🔴 R-23 / C-12 (14:10) — **PR-9's SECOND OUTCOME. Refusal restoration is NOT the route by which the attack is removed. At matched dose, arms that restore ZERO refusal remove exactly as much attack — and on Qwen3, MORE. "`demo_processing_only` works BY restoring refusal" is REFUTED.**

**Artifacts:** re-cut of `p4bj_*` / `q4bj_*`; no new compute. **PR-9 was committed (`696cef65`) before
these cells were read, and pre-declared this outcome as "the one that would most change the story".**

#### The decisive cell: Llama, `n_examples = 4`

| arm | refusal rise | **ΔASR** |
|---|---|---|
| **`demo_processing_only`** | **+0.2250** (9 rows) | **−0.1750** |
| `legacy_all_query` | −0.0500 | **−0.1750** |
| `response_query_only` | −0.0500 | **−0.1750** |

**Baseline: 8 attacks in 40 rows. All three arms removed the same 7 of 8.** Arm-vs-arm gaps are
**0.0000** — not "within margin", *identical*. **One arm restored nine rows of refusal and two
restored none, and it bought exactly zero additional attack removal.**

#### The full dose-matched picture

**LLAMA** (refusal rise / ΔASR):

| dose | attacks | `demoproc` | `legacy` | `respq` |
|---|---|---|---|---|
| 1 | 2/40 | +0.0000 / −0.0500 | −0.0250 / −0.0250 | −0.0750 / +0.0000 |
| 2 | 5/40 | +0.0750 / −0.1250 | +0.0000 / −0.1000 | −0.0250 / −0.0750 |
| **4** | 8/40 | **+0.2250 / −0.1750** | **−0.0500 / −0.1750** | **−0.0500 / −0.1750** |
| 8 | 10/40 | +0.3500 / −0.2500 | −0.0250 / −0.2000 | −0.0250 / −0.1750 |

**QWEN3 — and here it points the other way:**

| dose | attacks | `demoproc` | `legacy` | `respq` |
|---|---|---|---|---|
| **8** | 8/40 | **+0.2000 / −0.1500** | **+0.0000 / −0.2000** | **+0.0000 / −0.2000** |

**At the highest Qwen3 dose, the arm restoring +0.2000 refusal removes LESS attack (−0.1500) than the
two arms restoring none (−0.2000 each), and both gaps (0.0500) clear the 0.0417 margin.** Refusal
restoration is not merely unnecessary there — it coincides with *less* removal.

#### ⛔ What is corrected

**C-12. The claim "`demo_processing_only` works by restoring refusal" is WITHDRAWN.** R-19 introduced
that framing ("*knocking out demonstration processing does not quietly disable the attack — it puts
the refusal back*") and R-20/R-22 built on it. **It does put the refusal back. That is not how it
removes the attack.**

**What SURVIVES, unchanged and still cross-model:**

* `demo_processing_only` is the **only** scope of four, on **either** model, that restores any refusal
  at all — **14/25 and 8/20 killed-by-refusal against 0 in all six other cells** (R-19, R-20, R-21).
* On Llama that restoration is a clean monotone dose-response, **+0.0000 → +0.3500** (R-22).
* The concept binding **survives** the intervention on both models (R-16, R-17).

**What is now REFUTED:**

* That refusal restoration is the **mechanism of attack removal**. **It is a second, distinct effect of
  the same intervention** — real, unique to `demoproc`, dose-scaling on Llama, and **causally
  disconnected from the ASR drop it was assumed to explain.**

**At `n = 8` on Llama `demoproc` does remove more than the controls** (−0.2500 vs −0.2000/−0.1750,
gaps 0.0500/0.0750, both clearing margin). **So refusal may contribute at the top dose.** But the bulk
of removal is present at every dose in arms with zero refusal, and the Qwen3 sign is opposite. **A
contribution at one cell of one model is not a mechanism.**

#### On the cell PR-9 was actually designed around

**`n = 1` is UNDERPOWERED and the inference is declined, exactly as pre-registered.** Llama baseline
there is **2 attacks in 40 rows (0.0500 < 0.10)**; `demoproc` removed both, which is simultaneously
"100% of the attack" and "2 rows". **PR-9 committed in advance to declining this cell in both
directions, and it is declined** — the verdict above rests on the well-powered `n = 4` and `n = 8`
cells and the pre-specified control arms, not on it.

⚠ 40 rows/cell. ⚠ `kw_refusal` is lexical. ⚠ Controls are not inert: R-21 showed they remove attack by
**coherent non-compliance**, which remains unexplained — **this phase now has a mechanism for the
refusal it can no longer attribute the attack removal to, and no mechanism for the removal itself.**

---

### PR-9 (14:05) — **Pre-registered before running: do REFUSAL RESTORATION and ATTACK REMOVAL move together across dose, or do they come apart?**

R-22 handed this phase a natural experiment it did not have to run: on Llama, `demo_processing_only`
restores **exactly zero** refusal at `n_examples = 1` and **+0.3500** at `n = 8`. **The dose axis
therefore contains a cell where the proposed route is switched OFF while the intervention is still
fully applied.** That is a far better test of "refusal restoration is the route" than conditioning on
which rows refused, which would condition on a **post-treatment collider**.

**The question.** At `n_examples = 1` on Llama, where refusal restoration is zero, **is the ASR drop
also zero?**

**Prediction if refusal restoration IS the route:** ΔASR at `n = 1` is **within `MARGIN_VS_BASELINE
= 0.0521` of zero**, and the ASR drop grows with `n_examples` alongside the refusal rise.

**Prediction if they are SEPARATE:** ΔASR at `n = 1` is **below −0.0521** — the attack is removed at a
dose where **no refusal was restored at all**. That would mean `demo_processing_only` has **two
distinct effects**, and the refusal restoration is a **co-occurring phenomenon rather than the
mechanism of attack removal**.

**⛔ I am pre-committing that the second outcome is the one that would most change the story, and that
I will report it as such.** R-19 through R-22 have been accumulating support for a refusal-based
route; **this is the cell that can take it apart**, and it exists only because R-22's dose cut created
it. **A result here that separates the two would narrow every "route" claim in this phase to "one of
at least two effects".**

**Controls, pre-specified.** The same per-dose ΔASR curve for `legacy_all_query` and
`response_query_only` — arms with **zero** refusal restoration at every dose (R-21/R-22). **Whatever
they do at `n = 1` is what attack removal looks like with the refusal route definitionally absent**,
and is the correct comparison for `demoproc`'s `n = 1` cell.

**⛔ Power, stated first.** 40 rows/cell, finest step **0.025**, margin ≈ **2.1 rows**. Baseline ASR is
itself dose-dependent and at `n = 1` may be low enough that **there is little attack to remove** — in
which case ΔASR near zero is **uninformative, not confirmatory**. **I will report the per-dose
baseline ASR beside every delta, and if the `n = 1` baseline is under ~0.10 (4 rows) I will call the
cell UNDERPOWERED and decline the inference in both directions.**

Qwen3 is reported too, but PR-8 already refuted the dose ordering there, so **Qwen3 cannot confirm or
refute this and is descriptive only.** Zero new compute.

---

### R-22 (13:40) — **PR-8 SPLITS BY MODEL: a textbook dose-response on Llama (0 -> +0.3500, monotone, 6.7x the margin), and a REFUTATION on Qwen3 by my own endpoint rule. Reported as one confirmation and one refutation, not as a trend.**

**Artifacts:** re-cut of `p4bj_*` and `q4bj_*` (no new compute). Cells verified balanced: **40 rows per
`n_examples` level, 4 domains per level, on both models.**

#### LLAMA — confirmed, and the shape is the finding

Refusal rise under `demo_processing_only` vs the **same-`n_examples`** baseline:

| n_examples | baseline | demoproc | rise | **step, in rows** |
|---|---|---|---|---|
| **1** | 3/40 | 3/40 | **+0.0000** | **+0 rows** |
| 2 | 3/40 | 6/40 | +0.0750 | +3 rows |
| 4 | 2/40 | 11/40 | +0.2250 | +9 rows |
| **8** | 1/40 | 15/40 | **+0.3500** | **+14 rows** |

**Monotone non-decreasing: TRUE. Endpoint contrast +0.3500 — 6.7x the 0.0521 margin.** The steps are
0, 3, 9 and 14 rows, far outside the one-to-two-row wobble PR-8 declared as noise in advance.

**The most informative cell is `n_examples = 1`, where the rise is EXACTLY ZERO.** With a single
demonstration, knocking out demonstration processing restores **no refusal at all**. **The effect is
not a property of having a demo block — it is a property of having ACCUMULATED demonstrations**, and
it grows with how many there are.

**Controls behave as pre-specified**: `legacy` end-to-end **−0.0000** and `respq` **+0.0500**, both
**within margin**, both non-monotone, both hovering at or below zero at every level. **Prompt length
and demo-block size therefore do not explain the Llama curve** — those grow with `n_examples` for the
control arms too, and the control arms do nothing.

#### ⛔ QWEN3 — REFUTED by the rule I wrote before looking

| n_examples | baseline | demoproc | rise | step, in rows |
|---|---|---|---|---|
| 1 | 0/40 | 7/40 | **+0.1750** | +7 rows |
| 2 | 1/40 | 2/40 | **+0.0250** | +1 row |
| 4 | 1/40 | 6/40 | +0.1250 | +5 rows |
| 8 | 0/40 | 8/40 | +0.2000 | +8 rows |

**Monotone: FALSE. Endpoint contrast +0.0250 — WITHIN the 0.0521 margin.** PR-8 states plainly:
*"Refuted if the rise is flat across levels (within margin end to end), or decreasing."* **It is flat
end to end. The dose-response hypothesis is REFUTED on Qwen3, and I am applying my own rule rather
than reaching for the reading I would prefer.**

**What is nonetheless true on Qwen3, and must not be inflated into a rescue:** the rise is **positive
at all four levels** (+7, +1, +5, +8 rows), which is consistent with R-20's overall +0.1312 and shows
the refusal restoration is real at every dose. **What fails is the ORDERING, not the effect.** The
non-monotonicity is driven by the `n=2` cell at **+1 row**, which is *precisely* the one-row wobble
PR-8 pre-declared as unresolvable — **but a curve whose shape depends on cells that thin cannot be
claimed as a dose-response either way.** The honest verdict is the pre-registered one: **refuted.**

#### What this does and does not change

* **R-19/R-20/R-21 are untouched.** They claim `demo_processing_only` restores refusal and no other
  scope does. R-22 tested a *mechanism* for that, not the effect itself, and the effect is positive at
  every dose on both models.
* **The mechanism is established on Llama only.** *"Demonstrations suppress refusal cumulatively, and
  masking their processing lifts that suppression in proportion to how much of it there was"* now has
  strong single-model evidence and **an explicit cross-model failure**. It cannot be stated as a
  two-model result. **This is exactly the asymmetry R-20 warned about in the other direction**, where
  the ASR ordering reversed between models while refusal held.
* **No follow-up is launched to rescue the Qwen3 curve.** Per the standing instruction, a failed gate
  stops that branch. Raising Qwen3 cell counts to resolve a one-row wobble would be a search for a
  result, not a test of one.

⚠ 40 rows/cell; finest resolvable step 0.025. ⚠ `kw_refusal` is lexical. ⚠ Llama baseline refusal
*falls* with `n_examples` (3, 3, 2, 1 of 40) while the demoproc rise climbs — so the two move apart,
but the baseline trend is itself only a 2-row spread and is not interpreted.

---

### PR-8 (13:35) — **Pre-registered before running: DOSE-RESPONSE. If the demonstrations are what suppress refusal, then knocking out demo processing should restore MORE refusal when there are MORE demonstrations to knock out.**

R-19/R-20/R-21 establish **that** `demo_processing_only` restores refusal and no other scope does.
They do not say **why**. The mechanistic reading is: *the demonstrations suppress refusal while they
are being processed, and masking demo->demo attention prevents that suppression.* **That reading makes
a quantitative prediction the existing data can already test**, because `n_examples ∈ {1, 2, 4, 8}` is
a bank axis and every arm is balanced across it (40 rows per level, 160 total).

**Prediction (fixed before looking).** The refusal rise under `demo_processing_only`, measured against
the same-`n_examples` baseline, is **monotonically non-decreasing in `n_examples`**, and is **larger at
`n_examples = 8` than at `n_examples = 1`** by more than the arm-vs-baseline margin
`MARGIN_VS_BASELINE = 0.0521`.

**Refuted if** the rise is flat across levels (within margin end to end), or **decreasing**. A flat
dose-response would mean the effect is about the *presence* of a demo block rather than its *content
volume*, which is a different mechanism and would have to be reported as such.

**Control arms, pre-specified.** The same curve is computed for `legacy_all_query` and
`response_query_only`. Those arms restore **zero** refusal overall (R-21: 0/24, 0/24, 0/19, 0/20), so
their curves should be **flat at zero**. If a control curve also rises with `n_examples`, the effect is
about prompt length or demo-block size and **not** about demonstration processing.

**⛔ Power is the binding constraint here and I am stating it before, not after.** Each cell is **40
rows**, so the finest resolvable step is **1/40 = 0.025** and a single row moves a cell by that much.
`MARGIN_VS_BASELINE = 0.0521` is **≈ 2.1 rows**. **A monotone-looking curve built from steps of one or
two rows is inside the noise and will be reported as SUGGESTIVE ONLY.** I will report the endpoint
contrast (n=8 vs n=1) against the margin as the primary read, and the shape as description.

**Both models, and they are separate tests.** Llama and Qwen3 are reported independently; a result on
one is not a result on both. Zero new GPU: this is a re-cut of artifacts already committed
(`p4bj_*`, `q4bj_*`).

---

### 🏆 R-21 (13:12) — **PR-7 OUTCOME A: the degeneracy control HOLDS in all 8 cells. The zero-refusal arms kill by COHERENT NON-COMPLIANCE, not by breaking the generator. My own R-20 caveat does not bite.**

**Artifact:** `outputs/boombness/kill_route_breakdown/krb_20260825_131040_3620206/kill_route_breakdown.json`
**Producing script:** `src/boombness/kill_route_breakdown.py` (new). **No GPU, no API** — both
instruments are deterministic.

| cell | killed | **REFUSAL** | **DEGENERATE** | COHERENT NON-COMPLIANCE | short | scorable |
|---|---|---|---|---|---|---|
| **llama:demoproc** | 25 | **14** | **0** | 11 | 0 | 1.000 |
| llama:legacy | 24 | **0** | **0** | 24 | 0 | 1.000 |
| llama:respq | 24 | **0** | **0** | 24 | 0 | 1.000 |
| llama:qpre | 18 | **0** | **0** | 18 | 0 | 1.000 |
| **qwen3:demoproc** | 20 | **8** | **0** | 12 | 0 | 1.000 |
| qwen3:legacy | 19 | **0** | **0** | 19 | 0 | 1.000 |
| qwen3:respq | 20 | **0** | **0** | 20 | 0 | 1.000 |
| qwen3:qpre | 15 | **0** | **0** | 15 | 0 | 1.000 |

**Zero degenerate rows in 165 killed attacks across 8 cells**, and **`frac_scorable = 1.000`
everywhere** — so the short-row blindness that `coherence_gate`'s own header warns about (the gate is
blindest exactly on refusal-heavy arms) **did not apply to a single cell**. Nothing was UNSCORABLE and
nothing passed by an empty-set technicality.

#### The control was mutation-verified, because "all clean" is what a broken detector also says

| check | result |
|---|---|
| `"the bomb " * 8`, `"carrot " * 20`, `"go now " * 15` | **True** (fires) |
| coherent refusal prose | **False** |
| `degeneracy("I cannot help.")` | **None** — unscorable, *not* "clean" |

And the real rows are **nowhere near** the thresholds. On `qwen3:respq`, the worst-smelling cell
(134/160 distinct, median 322 chars vs 584 baseline):

| statistic | median | **worst row** | threshold |
|---|---|---|---|
| `uniq_word_ratio` | 0.781 | **0.640** | < 0.45 |
| `trigram_repeat` | 0.000 | **0.068** | > 0.30 |
| `top_word_frac` | 0.125 | **0.177** | > 0.25 |

**The Qwen3 zero-refusal completions are shorter and less varied than baseline — but they are
coherent, non-repetitive prose, not collapse.** Shorter is not degenerate, and R-20 was right to flag
the smell and right not to assume it.

#### What this settles

> **PR-7 Outcome A. Leg (b) of R-19/R-20 stands as written**: the zero-refusal arms remove a
> comparable amount of attack by **coherent non-compliance**. The "different routes" framing is
> **not** withdrawn, and the narrowing-to-Llama contingency (Outcome B) is **not** triggered.

**And the refusal asymmetry gets sharper, not softer.** `demo_processing_only` is the **only** arm in
any of the 8 cells producing **any** refusal at all — **14/25 on Llama and 8/20 on Qwen3, against
exactly 0 in all six other cells.** Note `qwen3:demoproc`'s row *verdict* reads
`COHERENT_NONCOMPLIANCE` only because that is the plurality label (12 > 8); **the discriminating fact
is 8 vs 0, not which bar is tallest.**

⚠ The classifier counts a short non-refusal row as DEGENERATE **on purpose** — biased *against* the
claim under test. No cell had one, so the policy never had to act. ⚠ `kw_refusal` is lexical: it
detects refusal *markers*. ⚠ Coherent non-compliance is a residual category — "neither refusal nor
degenerate" — and is not itself positive evidence of any particular behaviour.

---

### PR-7 (13:10) — **Pre-registered before running: does the kill in the ZERO-REFUSAL arms survive a degeneracy control, or is it generation collapse?**

R-20 recorded a caveat against my own arms: on Qwen3 `legacy` and `respq` fall to **144/160 and
134/160 distinct completions with medians 356 and 322 against a 584 baseline**. If their kills are the
model breaking rather than the model declining, then "same attack removed, different route" overstates
what the zero-refusal arms did, and **R-19/R-20's control leg is weaker than claimed**. This is
therefore a test I am running **against my own headline**, and it is pre-registered before it runs.

**Design.** For every killed attack in all **8 arm-model cells**, classify by two DETERMINISTIC,
drift-free instruments — the same discipline that made the refusal table trustworthy:

* `kw_refusal` — refusal markers (already used in R-19/R-20).
* `coherence_gate.degeneracy` — `uniq_word_ratio < 0.45`, `trigram_repeat > 0.30`, or
  `top_word_frac > 0.25`.

Three exclusive routes: **REFUSAL**, **DEGENERATE**, and **COHERENT NON-COMPLIANCE** (neither).

**`degeneracy()` returns `None` under 8 words, and I am not allowed to forget it.** The module's own
header documents that this makes the gate *blindest on refusal-heavy arms* — precisely the arms in
question — and that a run of 5-word refusals can post excellent coherence computed on an
unrepresentative tail. **`n_dropped_short` will be reported for every cell**, and any cell whose
scorable fraction falls below `MIN_SCORABLE_FRAC = 0.50` will be reported as **UNSCORABLE rather than
as coherent**. A cell with zero scorable rows passes the raw gate outright by IEEE-754 (`nan` fails no
comparison); that outcome is a **failure to measure**, and will be labelled one.

**Outcomes, fixed now:**

* **A — the control holds.** Coherent non-compliance is the majority route for `legacy`/`respq` on
  both models. R-19/R-20 stand as written.
* **B — the control is WEAKENED on one model.** Degenerate is the majority route for `legacy`/`respq`
  on Qwen3 but not Llama. **Then the cross-model claim "comparable attack removed by different
  routes" must be narrowed to Llama**, and R-20's ASR-equivalence leg is retired on Qwen3.
* **C — the control FAILS on both.** Then the zero-refusal arms never demonstrated a route at all,
  **the "different routes" framing is withdrawn**, and what survives is only the positive claim:
  `demo_processing_only` restores refusal.
* **D — unscorable.** Too few long completions to decide. **Reported as unmeasured; no outcome
  claimed.**

**This cannot strengthen R-20 and is not designed to.** The best case is that a caveat I raised
myself turns out not to bite. **`demo_processing_only`'s refusal rise (+0.1312 Qwen3, +0.1625 Llama)
is untouched by any outcome here**, since it is measured on refusal markers, not on coherence.

---

### 🏆🏆🏆 R-20 (12:40) — **PR-6 REPLICATES ON QWEN3, ON ALL THREE PRE-REGISTERED CONDITIONS. `demo_processing_only` is the ONLY scope of four, on EITHER model, that restores refusal — and on Qwen3 it does so while having the SMALLEST ASR effect and a NULL sign test.**

**Artifacts:** arms `q4b*` (jobs 779947-779951), judging `q4bj_*` (job **780012**).
**Provenance closed:** `openai/gpt-4o-mini` on **800/800** rows, `completion_sha256_16` joins on
**800/800**. **PR-6 was committed (`3d8f331c`) before any scalar below was loaded.**

**Qwen3 baseline: ASR 0.1313, keyword-refusal rate 0.0125** (read from `q4bj_A`, not assumed).

| arm | ΔASR | refusal rate | rise vs baseline | vs 0.0521 margin | killed | **of which refusal** |
|---|---|---|---|---|---|---|
| **`demo_processing_only`** | −0.0875 | **0.1437** | **+0.1312** | **ABOVE** | 20 | **8 (40%)** |
| `legacy_all_query` | −0.1062 | **0.0000** | −0.0125 | within | 19 | **0 (0%)** |
| `response_query_only` | −0.1125 | **0.0000** | −0.0125 | within | 20 | **0 (0%)** |
| `query_prefill_only` | −0.0625 | **0.0000** | −0.0125 | within | 15 | **0 (0%)** |

**PR-6 condition 1 — HOLDS.** `demoproc` rise **+0.1312**, 2.5x the 0.0521 margin.
**PR-6 condition 2 — HOLDS.** legacy and respq both at **−0.0125**, well inside margin. So is `qpre`.
**PR-6 condition 3 — HOLDS.** `demoproc` **40% > 25%**; legacy and respq both **0%**.
**Refutation conditions: neither triggered.** ✅ **REPLICATED.**

#### 🔴 Why this replication is worth more than a matching table

**On Qwen3, `demo_processing_only` has the SMALLEST ASR effect of the three effective arms
(−0.0875 vs −0.1062 and −0.1125) and its domain sign test is a flat NULL (`p = 1.00000`, 5 of 9
informative domains negative).** On Llama it had the largest delta and `p = 0.00195` with all ten
domains negative. **The ASR story between the two models is not merely different, it is reversed —
and the refusal story is identical.**

**PR-6 pre-committed both of those as NOT counting**, before they were seen. That is the entire value
of having written it first: the magnitudes were declared irrelevant while they were still unknown, and
they turned out to point the other way. **A post-hoc reading of this data could have told either
story.**

Every ASR pair on Qwen3 is **EQUIVALENT** at the 0.0417 margin except `qpre` vs legacy (0.0437) and
`qpre` vs respq (0.0500) — both marginal. **So on Qwen3 the four scopes are essentially
indistinguishable by ASR, and completely separated by refusal.**

> **Across two model families and four scopes — eight arm-model cells — exactly one thing restores
> refusal, and it is knocking out demonstration processing. Every other scope removes comparable
> amounts of attack with the refusal rate at or BELOW baseline.**

#### ⚠ A new caveat, pointing at the OTHER arms

The degeneracy pattern **inverts between models**, and on Qwen3 it lands on legacy/respq:

| arm | distinct completions | median n_chars | stop=length |
|---|---|---|---|
| baseline | 159/160 | 584 | 42 |
| **`demo_processing_only`** | **159/160** | **817** | 99 |
| `legacy_all_query` | **144/160** | **356** | 14 |
| `response_query_only` | **134/160** | **322** | 7 |

**On Qwen3 it is `legacy` and `respq` whose completions collapse** — 16 and 26 duplicate rows, medians
roughly *half* the baseline — while `demoproc` stays as distinct as baseline and runs *longer*. On
Llama the collapse was `demoproc`'s (141/160, 27 short rows, all keyword-refusals). **So the "kill" in
the zero-refusal arms is at least partly generation degradation, on at least one model.** That is a
caveat against `legacy`/`respq` being clean, not against the refusal finding — but it means **"same
amount of attack removed" is doing less work than the raw ASR equality suggests**, and it is recorded
here rather than left for a reviewer.

⚠ `demoproc`'s Qwen3 ASR effect is a **null on the domain sign test**; only its refusal effect
replicates. ⚠ Lexical G = 1 throughout. ⚠ Refusal is `kw_refusal`, deterministic and drift-free, but
**lexical** — it detects refusal *markers*, not refusal.

---

### PR-6 (12:30) — **Pre-registered BEFORE the Qwen3 Phase-4B judge output was read. Fixes what would count as replication of R-19, and what would refute it.**

Written while job **780012** was still judging; the artifacts existed but no scalar from them had been
loaded. R-19's surviving claim (as corrected by C-11) is **not** about effect magnitudes, so this
pre-registration is not either.

**The claim under test.** *Scopes that remove comparable amounts of attack do so by different routes,
and `demo_processing_only` is the one that works by restoring refusal.*

**Replication requires ALL THREE:**

1. **`demo_processing_only` raises the keyword-refusal rate above the Qwen3 baseline**, by more than
   the arm-vs-baseline margin `MARGIN_VS_BASELINE = 0.0521`.
2. **`legacy_all_query` and `response_query_only` do NOT** — each within ±0.0521 of the Qwen3
   baseline refusal rate.
3. **The refusal share among killed attacks is ordered `demoproc > legacy` and `demoproc > respq`**,
   with `demoproc` above 25% and both others below it.

**Refuted if:** `demoproc`'s refusal rate is within margin of baseline, **or** either other arm also
rises above margin (which would make refusal-restoration a generic knockout effect, not a
demo-processing one).

**Explicitly NOT part of replication** — pre-committed so a favourable reading cannot be adopted after
the fact:

* **ASR deltas and their ordering.** C-11 established these sit inside the margin on Llama and cannot
  rank arms. **A different ordering on Qwen3 is not evidence of anything and will not be reported as
  such.**
* **The domain sign test reaching its floor.** Llama's `demoproc` hit `p = 0.00195` with all 10
  domains negative. **Qwen3 falling short of that is not a failed replication**, since the two models
  have different baseline ASRs and therefore different attainable evidence.
* **Any claim resting on `demoproc` vs `respq`**, which cleared the margin by 0.0020 on Llama.

**Population.** Same d10 bank (`368566acecdc350f`), same 160 rows, Qwen3-14B at band 7-17 with
`enable_thinking=false` — the band and flag used by the Qwen3 Phase-1 session, not re-tuned here.
**Baseline refusal rate is read from `q4bj_A` and is not assumed equal to Llama's 0.0563.**

---

### C-11 (12:20, 4h DEEP REVIEW) — **I ranked the arms by an ASR ordering that sits BELOW my own pre-registered margin. `demo_processing_only` and `legacy_all_query` are EQUIVALENT on ASR; only the refusal route separates them.**

**Found by:** the deep review's independent recomputation — every R-19 scalar re-derived from the raw
judge rows without importing `phase1_decomposition`. **All figures reproduce exactly** (baseline
0.1562; deltas −0.1250 / −0.1500 / −0.1062 / −0.0250; k_inf 8/10/6/6; p 0.07031 / 0.00195 / 0.03125 /
0.68750). The error was not in the arithmetic — it was in what I let the ordering mean.

**The full pairwise table at PR-3's `MARGIN_ARM_VS_ARM = 0.0417`, which R-19 never printed:**

| pair | gap | verdict |
|---|---|---|
| **`demoproc` vs `legacy`** | **0.0250** | **EQUIVALENT** |
| `legacy` vs `respq` | 0.0188 | EQUIVALENT |
| `demoproc` vs `respq` | **0.0437** | distinguishable — **by 0.0020** |
| `demoproc` vs `qpre` | 0.1250 | distinguishable |
| `legacy` vs `qpre` | 0.1000 | distinguishable |
| `respq` vs `qpre` | 0.0812 | distinguishable |

**What is withdrawn.** R-19 presented `demo_processing_only` first with the largest delta and spoke of
"its margin over legacy". **There is no such margin.** 0.0250 is inside the band I fixed in PR-3
precisely to stop this, and PR-3's band was itself measured from re-judge spread. **Ranking three
arms by differences smaller than the instrument's reproducibility is exactly the failure the margin
exists to prevent, and I committed it in the same document that defines the margin.**

**`demoproc` vs `respq` clears the margin by 0.0020** — one prompt of 160 is 0.00625, so this
"distinguishable" verdict is **thinner than a single row**. It is reported as marginal and nothing
is built on it.

**What SURVIVES, and is strengthened.** The finding was never the magnitudes:

> **Three arms remove a statistically indistinguishable amount of attack — and one of them does it by
> restoring refusal while the other two do not touch the refusal rate at all.**

That is a *better* result than a ranking. The separating measurement is `kw_refusal`, a
**deterministic keyword detector** with no session drift, at **14/25 (56%) vs 0/24 vs 0/24** and
refusal rates **0.2188 vs 0.0312 vs 0.0125** against a **0.0563** baseline. Those gaps are an order of
magnitude clear of any margin. **The ASR equivalence is the control that makes the refusal
dissociation meaningful: same amount of attack removed, entirely different route.**

**Also corrected:** the R-19 length caveat spoke of `demoproc`'s "margin over legacy" being
length-carried. Restated — **`demoproc`'s length sensitivity is a fact about `demoproc`**
(−0.150 → −0.076 at ≥120 chars, vs flat legacy and respq), **not about a between-arm margin that does
not exist.**

---

### 🏆🏆🏆 R-19 (11:38) — **PHASE 4B AT k=10: three scopes remove the SAME amount of attack by THREE DIFFERENT ROUTES. `demo_processing_only` works by RESTORING REFUSAL; `legacy` and `response_query_only` kill just as many attacks with ZERO refusals.**

**Artifact:** `outputs/boombness/phase1_decomposition/p4bdec_20260825_113813_3430676/phase1_decomposition.json`
**Judging:** job 779926, prefix `p4bj`. **Provenance closed:** `judge_model_used = openai/gpt-4o-mini`
on **800/800** rows and `completion_sha256_16` joins the generation on **800/800** rows, all five arms.

#### The headline table (baseline ASR 0.1562, n = 160, 10 domains x 16)

| arm | ASR | delta | down/up | informative domains | p | floor | at floor? |
|---|---|---|---|---|---|---|---|
| **`demo_processing_only`** | 0.0063 | **−0.1500** | 25/1 | **10/10 all negative** | **0.00195** | 0.00195 | **yes** |
| `legacy_all_query` | 0.0312 | −0.1250 | 24/4 | 8/10, 7 negative | **0.0703** | 0.0078 | no |
| `response_query_only` | 0.0500 | −0.1062 | 24/7 | 6/10 all negative | 0.0312 | 0.0312 | yes |
| `query_prefill_only` | 0.1313 | −0.0250 | 18/14 | 6/10, 4 negative | **0.6875** | 0.0312 | no |

**The floor moved and the result survived it.** At k = 6 the sign test could not return anything
below 0.0625. At k = 10, `demo_processing_only` is negative in **all ten domains** — the maximum
evidence this design can produce — and `query_prefill_only` is now a **measured null (p = 0.6875)**
rather than an untestable one. That is what Phase 4B was for.

#### 🔴 The route is not the same, and this is the actual finding

The three effective arms remove **almost identical amounts of attack** (25, 24, 24 rows killed). They
do it by **completely different means**. `refused` here is `judge_boombness.kw_refusal()` — a
**deterministic keyword detector, not the LLM judge** — so unlike every ASR in this sprint it carries
**none** of the judge's measured session drift.

| arm | attacks killed | **of which judged REFUSAL** | new refusals overall | arm refusal rate |
|---|---|---|---|---|
| **`demo_processing_only`** | 25 | **14 (56%)** | **28** | **0.2188** |
| `legacy_all_query` | 24 | **0 (0%)** | 4 | 0.0312 |
| `response_query_only` | 24 | **0 (0%)** | 0 | 0.0125 |
| — baseline — | — | — | — | 0.0563 |

> **Knocking out demonstration processing does not quietly disable the attack — it puts the refusal
> back.** The other two scopes suppress exactly as much attack while leaving the refusal rate at or
> *below* baseline. **A single ASR number would have called these three arms the same result.**

**This is the same locus the sprint already found from the other direction.** The V2 continuation
concluded that **refusal-suppression, not the concept representation, is the causal locus**. R-16 and
R-17 then showed the concept mapping **survives** `demo_processing_only` on both models. R-19 supplies
the missing half: **the arm that preserves the mapping is the arm that restores refusal.** Three
independent measurements, one mechanism.

#### ⛔ Corrections and limits — including one against a previous result

**⚠ The PR-1 primary comparison FLIPS on this bank, and I am reporting it as a partial
non-replication rather than choosing the bank I prefer.** R-10 (k = 6) found
`response_query_only` at **46%** of legacy with gap **0.0729 > 0.0417**, and declared the primary
comparison **NOT equivalent** (Outcome B). Here respq is **85%** of legacy with gap **0.0188**, which
**passes** the same pre-registered margin. **Outcome B does not replicate at k = 10.** The
n_examples-matched, domain-balanced bank is the better-powered instrument, but the two banks are not
the same population, and I am not entitled to retro-fit which one counts. **The claim "response-query
knockout is a weak partial" is hereby WITHDRAWN.**

**⚠ `demo_processing_only`'s margin over legacy is length-carried; its refusal signature is not.**
Its delta falls from **−0.150 raw to −0.076** conditioning at ≥120 chars, while legacy (−0.125 →
−0.132) and respq (−0.106 → −0.115) are flat. It also has **27 rows under 120 chars** against 4 in
baseline, and **141/160 distinct completions** (7 duplicate groups, largest 7 identical 98-char
EOS completions) against 160/160 for baseline and respq. **All 27 short rows are keyword-refusals and
none scored ≥ 0.5** — so this is a stereotyped refusal collapse, not garbled generation. Length is
**post-treatment**: conditioning on it conditions on a **collider**, so neither number is the headline
alone. **The defensible statement is the refusal table, which needs no length conditioning at all.**

⚠ Llama only — Qwen3 Phase 4B not run. ⚠ Lexical G = 1. ⚠ `demo_processing_only`'s p is **at** its
floor: every informative domain agrees in direction and the magnitude cannot enter the p. It is a
sign test, a much stronger one than at k = 6, but still a sign test.

---

### C-10 (11:15) — **Expanding `DOMAINS` for Phase 4B silently broke the reproduction of the CANONICAL carrot bank. Caught by the test suite; fixed; both banks now regenerate byte-identically.**

**What broke.** `prompt_families._blocks()` read the module-level `demo_pools.DOMAINS` constant while
`build_demo_block()` indexes the **pools dict it was handed**. Taking `DOMAINS` from 6 to 10 for
Phase 4B (R-18) therefore made the generator ask a 6-domain pools file for a 10-domain domain list:

```
KeyError: 'warehouse_logistics|benign'
```

**This is worse than a test failure.** The canonical bank behind *every* result in this sprint —
`boombness_prompt_bank.jsonl` — **could no longer be regenerated from its own `demo_pools.json`**, and
regenerating it is precisely what §19's reproduction manifest requires. **A bank generator whose
output depends on a module constant rather than on its input is not reproducible.**

**How it was caught.** Not by inspection — by `tests/test_prompt_families_strict.py` going
`5 failed / 33 passed` in the tick's fast-test step, on a suite that was green at the previous commit.
**The value of running the science-critical tests every tick is that they fail on the commit that
breaks them, not three commits later.**

**The fix.** `_blocks(preset, domains=None)` now takes the domain list as an argument, and
`generate_bank` derives it from the pools actually loaded (`[d for d in DOMAINS if f"{d}|benign" in
pools]`, in `DOMAINS` order so row order is untouched, plus any pool domain not in the constant).
The `None` default falls back to the constant, so every existing caller is unchanged.

**Verification — byte-identity, not "it runs":**

| bank | committed sha256[:16] | regenerated sha256[:16] | families / violations |
|---|---|---|---|
| `boombness_prompt_bank.jsonl` (6 dom) | `7bf21cfbdc1966b0` | **`7bf21cfbdc1966b0`** | 336 / **0** |
| `boombness_prompt_bank_d10.jsonl` (10 dom) | `368566acecdc350f` | **`368566acecdc350f`** | 560 / **0** |

**No result is affected.** The d10 bank is byte-identical to the one jobs 779915-779919 already ran
against, so Phase 4B needs no resubmission, and the carrot bank was never regenerated during the
window in which the generator was broken. `test_prompt_families_strict.py` 5/5 pass; the four
science-critical suites 112/112.

---

### R-18 (11:07) — **D-10's gate: the four new domains are ACCEPTED, on their audit and before any effect size was computed.**

**Artifacts:** bank `data/boombness_prompts/boombness_prompt_bank_d10.jsonl` (+ `_meta.json`);
audit `outputs/boombness/tokenization_audit/audit_20260825_104550_1349216` (job 779914).

D-10 pre-registered that new domains are accepted or rejected **on their audit and never on their
effect size**, because choosing domains by how much they help is how a floor becomes a search. Both
gates were run and read **before a single behavioural number existed**:

* **alignment (`prompt_families.py --strict`)** — `2x2 families checked=560 violations=0`,
  `duplicate prompt_id rows dropped=0`. Exit 0.
* **tokenization (`tokenization_audit.py`)** — `rows ok=4560 bad=0`, **`token-alignment violations=0`**,
  `families=1680 checked=520 skipped_incomplete=1160`, `ambiguous=7`.

**Bank shape:** 4560 rows, **10 domains balanced at exactly 456 each**, conditions
`natural_doublespeak 1680 / benign_literal 1360 / direct_harmful 640 / concept_in_benign_ctx 640 /
direct_codeword 120 / benign_remap 120`. The behavioural population filter yields **160 rows = 10
domains x 16**, against 96 = 6 x 16 on the carrot bank.

**Why this run exists at all.** The Phase-1 domain sign test is **at its attainable floor**: with 6
domains and `lab_safety` netting zero, k = 5 and the floor is 0.0625, so *no arrangement of the data
could have produced a smaller p*. That is a SIGN TEST, not a p-value. At k = 10 the floor falls to
**2/2^10 = 0.00195**, so this is the run that lets the effect be *measured* rather than merely
signed. **It cannot rescue a null and it is not being run to: the estimator, the unit of
independence and the margins are all unchanged and were fixed in PR-1/PR-3.**

**Arms (jobs 779915-779919, all COMPLETED, all 160 rows, 16 per domain in all ten):**

| arm | scope_live | decode_live | prefill edits | decode edits | stop=length |
|---|---|---|---|---|---|
| `p4bA` baseline | — | — | — | — | 93/160 |
| `legacy_all_query` | 1.0 | 1.0 | 4,879,044 | 13,299,048 | 106/160 |
| `query_prefill_only` | 1.0 | **0.0** | 1,787,400 | **0** | 72/160 |
| `demo_processing_only` | 1.0 | **0.0** | 3,017,169 | **0** | 116/160 |
| `response_query_only` | 1.0 | 1.0 | 1,787,400 | 12,351,771 | 78/160 |

`scope_violations = {}` on every arm. **PR-1's subset check holds on this bank too:**
`qpre 1,787,400 + demoproc 3,017,169 = 4,804,569 <= legacy 4,879,044`, slack 74,475 — an inequality,
never an equality, for the reason C-3b established.

Judging is job **779926**, prefix `p4bj`, backend **pinned** to `openai/gpt-4o-mini` with the
pre-flight canary returning `1.0000` on all arms. **No result is read until it lands.**

---

### 🏆🏆🏆 R-17 (10:42) — **THE WITHIN-FAMILY BRIDGE REPLICATES ON QWEN3, AND MORE SHARPLY: `demo_processing_only` kills 10 attacks and loses binding on 0 of them, while losing binding on 5 families whose attack SURVIVED.**

**Artifact:** `outputs/boombness/binding_behaviour_bridge/qbridge_20260825_104155_3190213/binding_behaviour_bridge.json`
**Same script as R-16, zero changes** — `src/boombness/binding_behaviour_bridge.py`, pointed at the Qwen3
behavioural judge dirs (`q1j_*`, the R-12 session) and the Qwen3 probe arms (`q2*`).

| arm | families | killed | **lost \| killed** | lost \| NOT killed | reads as |
|---|---|---|---|---|---|
| **`demo_processing_only`** | 48 | **10** | **0 / 10 = 0.0000** | 5 / 38 = 0.1316 | **anti-associated** |
| `legacy_all_query` | 48 | 10 | 6 / 10 = 0.6000 | 22 / 38 = 0.5789 | independent, and a sledgehammer |
| `query_prefill_only` | 48 | 7 | 1 / 7 = 0.1429 | 6 / 41 = 0.1463 | independent to three decimals |

#### What replicates, and what is new

**The Qwen3 result is stronger than Llama's on the axis that mattered.** R-16's `0/7` rested on a thin
denominator. Here `demo_processing_only` kills **10** attacks and loses the binding on **none of
them** — while demonstrably being *able* to cost binding, since it took the mapping from **5 families
whose attack it did not kill**. On Llama the arm lost binding nowhere at all, so a sceptic could
answer "it simply never damages binding". **Qwen3 removes that escape: the arm damages binding, just
never on the families it disarms.**

**`legacy_all_query` is exposed as indiscriminate.** It loses the binding on **28 of 48 families**
(0.60 vs 0.58) — it is not selecting anything, it is flattening the demonstrations. That is the
arm the paper's original knockout used, and it is why an unscoped knockout cannot separate these two
things.

**`query_prefill_only` lands at 0.1429 vs 0.1463** — independence to three decimals.

#### The unified statement across both models

**In 6 of 6 arm×model cells, binding loss carries no positive information about attack death.**
Three cells are flat (independent), three point the wrong way (binding lost *more often* where the
attack survived). **Not one cell shows the positive association that "the mechanism runs through the
mapping" requires.**

> Within byte-identical demonstrations, on two model families, the intervention that disarms the
> attack is not the intervention that costs the concept mapping — and the arm that costs the mapping
> most (legacy) is the one that discriminates least.

⚠ Both models: probe is a forced-choice readout, not behaviour; lexical G = 1 (C-9d); the killed
counts (7–10 of 48) remain small, which is why the load is carried by the *not-killed* column.
Qwen3 probe liveness: `frac_rows_scope_live = 1.0`, `min_prefill_forwards = 44`,
`total_prefill_edits = 4,014,032`, `total_decode_edits = 0`, `scope_violations = {}`,
option-mass gate **PASS** (median 0.9990).

---

### 🏆🏆🏆 R-16 (10:16) — **THE WITHIN-FAMILY BRIDGE: the families whose ATTACK dies are NOT the families that lose their BINDING. The dissociation holds inside the same demonstrations, not merely on average.**

**Artifact:** `outputs/boombness/binding_behaviour_bridge/bridge_20260825_101613_3117657/binding_behaviour_bridge.json`
**Producing script:** `src/boombness/binding_behaviour_bridge.py` (new). **No GPU** — pure analysis over
artifacts already on disk.

**Why this design and not R-15's.** R-15 compared 48 probe rows against 96 behavioural rows *in
aggregate*, which can only say "binding survived on average while behaviour collapsed on average".
The bank makes the stronger design free: every probe row joins **1:1** to a behavioural row on the
family stem with a **byte-identical demo block**, and the 48 probe families are a strict **subset** of
the 96 behavioural ones (verified). **So each family contributes one behavioural row and one probe row,
under the same arm and the same demonstrations** — turning the dissociation into a 2×2 per family.

| arm | families | attacks killed | **binding lost \| attack killed** | binding lost \| attack NOT killed |
|---|---|---|---|---|
| **`demo_processing_only`** | 48 | 7 | **0 / 7 = 0.0000** | **0 / 41 = 0.0000** |
| `legacy_all_query` | 48 | 7 | 2 / 7 = 0.2857 | 4 / 41 = 0.0976 |
| `query_prefill_only` | 48 | 7 | **0 / 7 = 0.0000** | **8 / 41 = 0.1951** |

#### The two rows that matter

**`demo_processing_only` kills 7 attacks and loses binding on ZERO of 48 families.** Not zero among the
killed — **zero overall.** Its full contingency table has exactly two non-empty cells:
`attack_killed|binding_kept: 7` and `attack_not_killed|binding_kept: 41`. **There is no family anywhere
in the population where this arm cost the mapping.** Rule-of-three upper bound on its binding-loss
rate: **≤ 0.0625**.

**`query_prefill_only` is the sharpest, because it points the wrong way.** It loses binding on **8 of
the 41 families whose attack it did NOT kill**, and on **0 of the 7 it did**. **Binding loss and attack
death are not merely independent here — they are anti-associated.** An arm that damaged behaviour *by*
damaging the mapping could not produce that table.

> **Within the same demonstrations, the attack dies where the mapping survives.** R-15 established the
> dissociation between two populations; this establishes it **family by family**, which is the design
> the plan asked for and the one a reviewer would demand.

#### ⛔ The limit, and it is the honest one

**Only 7 of 48 families had an attack to kill.** The probe families are a subset chosen by query kind,
not by attackability, and baseline ASR on them is low. **`0/7` is a small denominator**, and on its own
it would be weak evidence. What carries the result is the *other* column: **`demo_processing_only` loses
binding on 0 of 48**, and `query_prefill_only`'s losses land entirely among families whose attack
survived. **Those are 48-family statements, not 7-family ones.**

⚠ Llama only; lexical G = 1 (C-9d); binding is a forced-choice readout, not a behavioural measure. The
Qwen3 probe (779891–779895) is running and will be put through the identical script.

---

### 🏆🏆🏆 R-15 (10:15) — **PHASE 2 RESULT: THE BINDING SURVIVES. The arm that removes ~75 % of attack success does NOT destroy the codeword→concept mapping — it takes it from 0.875 to 1.000. This is a representation ≠ behaviour dissociation AT THE POINT WHERE THE INTERVENTION WORKS.**

**Artifacts:** `outputs/boombness/score_behavior/p2{A,_legacy_all_query,_query_prefill_only,_demo_processing_only,_late}_20260825_*`
— 5 arms × **48 rows** (the full `semantic_forced_choice` ∧ `natural_doublespeak` core-2×2 population),
Llama, band L6–14, all COMPLETED `0:0`, **`frac_rows_scope_live = 1.0`, zero scope violations, zero
failures on every arm.** Option mass **0.368–0.599** — every arm above C-7's 0.05 gate, so every number
below is a real decision margin rather than a tail ordering.

**The probe asks what the codeword means, from the same demonstration block the behavioural row uses.
Binding = the model answers with the mapped CONCEPT rather than the literal codeword.**

| arm | binding accuracy | Δ | median margin | Δ margin (paired, 95 % CI) | option mass | down/up |
|---|---|---|---|---|---|---|
| `A_baseline` | **0.8750** | — | 3.4234 | — | 0.5414 | — |
| `legacy_all_query` | 0.8542 | −0.0208 | 1.0816 | **−2.557 [−3.244, −1.871]** | 0.3681 | 6/5 |
| `query_prefill_only` | 0.7708 | −0.1042 | 1.2103 | **−2.172 [−2.923, −1.420]** | 0.4311 | 8/3 |
| **`demo_processing_only`** | **1.0000** | **+0.1250** | 2.6589 | −0.897 [−1.580, −0.214] | 0.5987 | **0/6** |
| `late` control (20–28, same scope) | 0.8750 | +0.0000 | 3.2015 | −0.166 [−0.263, −0.069] | 0.5303 | **0/0** |

#### The decisive row, and it goes the opposite way to the hypothesis

**`demo_processing_only` is the arm that suppresses the attack** — Δ ASR **−0.1250** on Llama and
**−0.1562** on Qwen3, ~75–94 % of the legacy effect, and the only arm that beats its matched control
after C-9's length correction. **On the binding probe it does not degrade the mapping at all. It
rescues every row that was failing:**

```
baseline binding failures: 6 of 48
demo_processing_only:      0 down / 6 up   ->  accuracy 0.8750 -> 1.0000
late control:              0 down / 0 up
McNemar exact: p = 0.0312  (= 2/2^6, the attainable floor at 6 discordants -> a SIGN TEST)
```

**All six rescued rows were near the boundary and are pushed decisively positive** (baseline margins
−0.31 … −1.36 → +0.39 … +3.39), **while the late control leaves the same six negative** (−0.53 …
−1.57). So the rescue is band-specific, not a generic consequence of masking demonstration attention
somewhere.

> **The chain `demonstrations → response-time retrieval → binding → behaviour` does not hold. The
> intervention that removes three quarters of the attack leaves the semantic mapping fully intact —
> indeed perfect — and the late control shows the same intervention outside the band does neither.**
> **Representation and behaviour are separable *at the exact point where the causal intervention
> works*.** That is the same dissociation the previous sprint recorded for `d_surface`, now found for
> the retrieval mechanism itself rather than for a fitted direction.

#### ⚠ Where the arms DO cost something, and why it is not the mapping

Every arm reduces the *confidence* margin — `legacy` **−2.557**, `qpre` **−2.172** — and both of those
arms also lose binding accuracy (0.854, 0.771). **`demo_processing_only` has the smallest margin loss
of the three treatment arms (−0.897) and the only positive accuracy change.** So the arm that hurts
behaviour most hurts the mapping least. **The two quantities are not merely dissociated; they move in
opposite directions across arms.**

#### ⛔ What this does NOT establish — stated before anyone quotes it

* **One model.** Llama only. Qwen3 has not been run on the probe, and R-12 is what made
  `demo_processing_only` decisive in the first place — **the dissociation is not cross-model until it
  is.**
* **A different population from the behavioural result.** 48 forced-choice rows against 96 behavioural
  rows. They share families and demonstration blocks by construction (PR-2's 1:1 join), **but no row is
  in both**, so this is a between-population comparison, not a within-row one. **A within-row link is
  the stronger design and it has not been run.**
* **The p is at its floor.** `p = 0.0312 = 2/2⁶` on six discordants — **a sign test.** The magnitude
  cannot enter it, and PR-3's rule applies: quote the effect, quote the floor beside the p.
* **No probe-specific margin was pre-registered.** PR-2 fixed the *group*; it did not fix an equivalence
  margin for binding. **So the accuracy and margin figures are reported as magnitudes with CIs, and no
  pass/fail verdict is claimed on them.**
* **Lexical G = 1** (C-9d) applies here unchanged: one codeword, one concept.
* **Accuracy 1.0000 is a ceiling.** With baseline at 0.875 there were only six rows available to move,
  so "perfect binding" describes 48 rows of one lexical pair, not a general property.

---

### ⛔⛔⛔ C-9 (10:10) — **THE SECOND 4-HOUR REVIEW: all ~40 scalars of R-10 and R-12 reproduce at full precision, and FOUR of the claims built on them are withdrawn or narrowed. The core ordering survives and is in one respect strengthened.**

**Arithmetic and provenance are clean.** Every claimed scalar recomputed independently from the 16
`results.jsonl` files without touching the artifacts: both baselines, all 15 arm deltas, every
down/up count, both refusal sets, both primary gaps, every domain sign test and its floor — **all
MATCH.** Integrity: 16/16 judge dirs `DONE`, 96 rows, 0 duplicate `prompt_id`s, 0 null scores,
`judge_model_used = openai/gpt-4o-mini` on 96/96 of every arm, and
**`judge.completion_sha256_16 == sha256(gens.generation)[:16]` in 96/96 rows across all 16 arm/gens
pairings.** *(That last check is new and is the strongest provenance evidence this project has: the
judged text is provably the generated text, row by row.)*

#### ⛔ C-9a — "EXACTLY equal to the late-layer control — to the prompt" is WITHDRAWN

R-12 asserted identity and then extended it to mechanism (*"doing the same thing at layers 25–35 does
the same thing"*). **It is a balanced-discordance tie, not identity:**

| pair | same label | discordant | identical generations |
|---|---|---|---|
| `respq` vs `late11` | **88/96** | **4 up / 4 down** | **0/96** |
| `qpre` vs `late11` | **92/96** | 2 / 2 | **0/96** |

**And a tie is the most likely single outcome under the null:** P(exact tie | 8 discordants) =
**0.2734**, P(tie | 4) = **0.3750**; both arms landing on zero jointly ≈ **0.10 with no shared
mechanism at all.** Exact CIs: `respq − late11` **[−0.0572, +0.0572]**, `qpre − late11`
**[−0.0360, +0.0360]**.

> **The surviving statement is the weaker one: neither response-side arm is DISTINGUISHABLE from its
> late-layer control at n = 96.** The "to the prompt" wording and the mechanistic gloss are withdrawn.
> ✅ *Also checked and negative:* `respq` and `qpre` are **not** the same arm misconfigured — 86/96 same
> label, 1/96 identical generation, distinct flip sets.

#### ⛔ C-9b — on Qwen3, `legacy`'s "beat" is carried by a LENGTH COLLAPSE. `demo_processing_only`'s is NOT.

Paired median completion-length ratio vs baseline, and rows shortened ≥ 30 %:

| arm | median ratio | rows shortened ≥30 % | **length-matched Δ (ratio ≥ 0.7)** |
|---|---|---|---|
| `legacy_all_query` | **0.6461** | **56/96** | **−0.0750** (n=40) |
| `respq` | 0.6447 | 55/96 | −0.0488 |
| `qpre` | 0.6965 | 49/96 | −0.0213 |
| **`demo_processing_only`** | **1.1424** ⬆ | **12/96** | **−0.1310** (n=84) |
| `late11` (control) | 1.0000 | 12/96 | −0.0714 (n=84) |

**13 of `legacy`'s 17 down-flips are length-collapsed rows**, and once length is matched `legacy`
(−0.0750) **no longer beats its control** (−0.0714). ⚠ PR-4's collider caveat applies to that
comparison as always.

**But `demo_processing_only` makes output *longer* (ratio 1.14) and shortens only 12 of 96 — the same
as the control — and it still beats the control on length-matched rows (−0.1310 vs −0.0714).**
**So the length confound that eats `legacy`'s Qwen3 advantage does not touch the decisive arm.** This
is a *strengthening* of the R-12 ordering, arrived at by a check designed to break it.

#### ⛔ C-9c — at the bank's REAL clustering unit, the Qwen3 arm-vs-control contrast does not survive

The bank is **6 domains × 2 bank_blocks × 2 family slots = 24 demonstration cells**, with the four
`n_examples` levels **NESTED** inside each cell (the smaller-n demo block is a *prefix* of the larger-n
one in **72/72** adjacent pairs). **So 96 prompts are not 96 units, and the domain is not the finest
honest cluster either.** Cell-clustered exact sign test on **arm minus matched control**:

| | Llama | Qwen3 |
|---|---|---|
| `legacy_all_query` | **p = 0.0117** | p = 0.2188 |
| **`demo_processing_only`** | **p = 0.0063** | p = 0.2188 |
| `respq` / `qpre` | 0.2668 / 0.7744 | 1.0000 / 1.0000 |

**On Llama, `demo_processing_only` beats its matched control at p = 0.0063 — the first sub-0.05 result
at a defensible unit anywhere in this phase.** On Qwen3 neither arm clears. **The cross-model claim is
therefore: the ORDERING replicates, the arm-vs-control significance does not.**

#### ⛔ C-9d — the entire result is lexical G = 1, and I never said so

Over all 96 prompts: `codeword`, `concept`, `demo_surface`, `query_surface`, `target_semantic`,
`condition`, `strength`, `consistency`, `role_style`, `query_kind` each have **n_distinct = 1**.
**One codeword, one concept, one framing — across all six "independent" domains.** The previous sprint
retracted E12 over exactly this (*"call it `d_surface_carrot_bomb`"*). **Every Phase-1 statement is a
statement about one lexical pair**, and that belongs beside the headline, not in a limits paragraph.

#### ✅ And two checks that came out FOR the result

* **`demo_processing_only`'s effect is not mostly refusal or truncation.** Decomposing its down-flips:
  Llama **15 = 3 refused + 3 length-collapsed + 12 NEITHER**, non-refused Δ **−0.1200** (n=75);
  Qwen3 **17 = 4 + 4 + 12 NEITHER**, non-refused Δ **−0.1358** (n=81). **The refusal elevation is real
  but it is not the mechanism** — most flips are neither.
* **Dose does not drive the ordering.** Spearman(median `hook_n_edits`, Δ) over the five treatment arms
  = **−0.40** (Llama), **−0.30** (Qwen3). The arm with the most edits is not the arm with the biggest
  effect — which is what the previous sprint's entire dose-confound literature would have predicted if
  it did.

---

### ✅ C-8 CLOSED / R-14 (09:38) — **the mask now fires on the forward-only readout path. Phase 2's instrument is live for the first time, and every guard that blocked it was right.**

Jobs **779838–779840**, all COMPLETED `0:0`, forced-choice probe rows, band L6–14, `--limit 8`:

| arm | rows | `frac_rows_scope_live` | prefill edits | `min_prefill_forwards` | violations | failures |
|---|---|---|---|---|---|---|
| `legacy_all_query` | 8 | **1.0** | 1 172 385 | 36 | `{}` | 0 |
| `query_prefill_only` | 8 | **1.0** | 489 600 | 36 | `{}` | 0 |
| `demo_processing_only` | 8 | **1.0** | 617 760 | 36 | `{}` | 0 |

**Subset check holds on the readout path too:** `489 600 + 617 760 = 1 107 360 ≤ 1 172 385`.

**`min_prefill_forwards = 36` rather than 9** is the C-8 fix visible in the artifact: with
`max_batch = 1` the scorer runs one forward per option variant, so 9 band layers × 4 variants = 36
hooked prefill forwards per row. **The number is a consequence of the fix, not a coincidence.**

> **Three guards stood between Phase 2 and a wrong number, and all three were right:** C-6's liveness
> ledger (would have reported a scoped intervention as a null), C-7's option-mass gate (would have
> produced a decision margin inside a 3 % tail), and C-8's batch-1 collision (would have crashed, and
> the tempting fix would have silently reinstated the instrument C-7 had just ruled out). **The phase
> has produced no probe number yet precisely because it refused to produce a wrong one.**

---

### 🔬 PHASE 2 FULL PROBE LAUNCHED (09:40) — jobs 779864–779868

Five arms × **48 rows** (the full `semantic_forced_choice` ∧ `natural_doublespeak` ∧ core-2×2 population),
Llama, band L6–14, `--expect-n 48`:

| job | arm | note |
|---|---|---|
| 779864 | `A_baseline` | — |
| 779865 | `C_legacy_all_query` | the incumbent scope |
| 779866 | `C_query_prefill_only` | |
| **779867** | **`C_demo_processing_only`** | **the arm R-10/R-12 make decisive** |
| 779868 | `D_late_demoproc` | **20–28, SAME scope as the decisive arm, layer-count matched (9 blocks)** |

**The late control is at the decisive arm's own scope**, not at `response_query_only`'s — because after
R-12 the comparison that matters is *"does `demo_processing_only` destroy the binding **more than the
same intervention at control layers does**"*. A control at a different scope would not answer that.

📌 **The pre-registered question, restated before any probe number exists:** `demo_processing_only`
carries the behavioural effect on **both** models (−0.1250 Llama, −0.1562 Qwen3) **while raising
refusal ~20×**. **If it also destroys the codeword→concept binding**, the chain
*demonstrations → binding → behaviour* has its first direct evidence. **If the binding survives while
behaviour collapses**, the suppression never went through the semantics at all — and that is the more
interesting result, because it would say the attack's representation and its behaviour are separable
even at the point where the intervention works. **Both outcomes are publishable; neither is the one to
hope for.**

---

### ⛔ C-8 (09:15) — **THE PROBE'S SCORER BATCHES AND EVERY KNOCKOUT HOOK IS BATCH-1. Both constraints were documented; nobody had joined them, and the pre-flight passed clean right before every row died.**

Probe smoke v2 (jobs **779796–779798**) **FAILED `1:0`**, all three knockout arms, **8 of 8 rows**:

```
failure_reasons: {"semantic_forced_choice:NotImplementedError:
                  ScopedAttentionKnockout supports batch size 1 only": 8}
n_generations: 0   n_result_rows: 0
```

**The C-6 fix is working** — `liveness_readout_only: True` appears in every summary, so the reduced
contract was recognised — and **the pre-flight passed clean** immediately before:
`{'n_rows': 8, 'no_demo_block': 0, 'infeasible_control': 0, 'dead_scope_span': 0}`. **Spans resolve
perfectly on forced-choice rows; the rows die at SCORING time.**

#### The collision, and both halves were written down

| side | fact | where |
|---|---|---|
| the scorer | `string_option_readout(..., max_batch: int = 16)` — *"One batched forward over `context + variant` per variant"* | `signals.py` |
| the hook | `raise NotImplementedError("... supports batch size 1 only")` — in **three** classes: `SubmodulePatch`, `AttentionKnockout`, `AllQueryAttentionKnockout` (and now `ScopedAttentionKnockout`) | `pair_common.py:320, 463, 556` |

**Neither is a bug. The defect is that nothing joined them**, and the `whole_answer` scoring mode that
batches has been the **default since 2026-08-18**. So the very first attempt to run *any* intervention
against *any* forced-choice readout was always going to fail — and this is the first time in the
project that anyone has tried.

#### The fix, and the option I deliberately did not take

`max_batch=(1 if _wants_knockout else 16)` at both readout call sites.

⚠ **The tempting alternative was `--readout-ids primary`**, which is batch-1 already and would have
made the error disappear without touching anything. **I did not take it.** `whole_answer` became the
default on 2026-08-18 *because* the single-token readouts were shown to live in a 1e-5 tail — falling
back to `primary` to dodge a batching constraint would have silently reinstated the weaker instrument
that C-7 has just finished ruling out on option mass. **Forcing batch 1 keeps the instrument the repo
chose and pays ≤16× more forwards on a 96-row population, which is nothing.**

Un-batched arms re-submitted as **779838–779840**. The baseline (779795) is unaffected — it never
requested a knockout, so it already ran at `max_batch=16` and stands.

⚠ **Recorded as the fourth guard-caught failure of this phase**, and the pattern is now explicit:
prev-C-6's dose metric, C-5's stale handle, C-6's missing ledger, C-7's option mass, and now this. **In
every case a guard refused rather than producing a plausible number, and in every case the guard was
right and my configuration was wrong.**

---

### ✅ R-13 / C-7 CLOSED (08:40) — **the probe kind is chosen ON THE GATE: `semantic_forced_choice` clears it by 15×. Phase 2 is unblocked on both counts.**

Jobs **779771 / 779772**, baseline only, no intervention, `natural_doublespeak`, n = 16 — run
**before** any intervention arm, so the instrument is selected on its validity rather than on its
effect.

| query kind | median option mass | p90 | max | frac > 1 % | gate |
|---|---|---|---|---|---|
| `semantic_one_word` *(what I originally picked)* | **0.0310** | 0.0820 | 0.0820 | 0.625 | ⛔ **BELOW** |
| **`semantic_forced_choice`** | **0.4687** | 0.8938 | 0.9257 | **1.000** | ✅ **OK** |
| `comprehension_usage` | **0.3443** | 0.4572 | 0.5181 | **1.000** | ✅ **OK** |

**`--min-option-mass` is 0.05.** Forced choice clears it by **15×** on the median and puts **every**
row above 1 %, against the unforced variant's 62.5 %. This is the concentration
`prompt_families.QUERY_KINDS` already documented (`as_is 1.4e-2 → forced 0.979` on the direct arm) —
now measured on the **headline condition**, which had never been measured.

> **📌 DECISION D-9: `semantic_forced_choice` is Phase 2's PRIMARY probe; `comprehension_usage` is the
> secondary readout for §5.3's specificity question.** Both clear the gate, so neither choice is being
> made on an effect size. `semantic_one_word` is **dropped** — not because it gave an unwelcome answer,
> but because a 3 % option mass cannot carry a decision margin at all.

⚠ **`--allow-low-option-mass` was not used and will not be.** C-7 said an instrument that fails its own
gate is a finding about the bank, not a threshold to lower. The instrument turned out to exist; had it
not, the honest output would have been that Phase 2's primary measurement is unavailable here.

#### Phase 2's blockers are now both resolved

| blocker | status |
|---|---|
| **C-6** — liveness ledgered only on the generation branch | ✅ **CLOSED** — hook proven to apply by AST; reduced contract with `n_prefill_forward` as proof-of-life; 124 tests |
| **C-7** — probe kind failed the option-mass gate | ✅ **CLOSED** — `semantic_forced_choice` at median 0.4687 |

**Probe smoke v2 launched: jobs 779795–779798** — baseline plus the **three prefill-measurable modes**
(`legacy_all_query`, `query_prefill_only`, `demo_processing_only`) on forced-choice rows, band L6–14,
`--limit 8`. `decode_only` and `response_query_only` are **not** submitted: C-6's fix refuses them at
argument time on a forward-only readout, the second because its reduction is identical to
`query_prefill_only` and would misname the intervention.

**The question this is being built to answer, restated before any number exists:** R-10 and R-12 show
`demo_processing_only` carries the behavioural effect on both models **while raising refusal 20×**.
**Does it also destroy the codeword→concept binding, or does it leave the mapping intact and simply
make the model refuse?** Those two answers mean very different things, and the probe is the only
instrument that separates them.

---

### ✅ C-6 CLOSED (08:40) — **the hook DID apply during the readout; only the ledger was missing. The serious branch is ruled out.**

C-6 named two possibilities and said which mattered: *"if the hook is not even entered on that path, any
forward-only 'intervention' result ever produced was actually a baseline."* **It was entered.**
**Verified independently by me, by AST rather than by reading:**

```
ExitStack `with` (the intervention contexts) spans lines 1723-1899
   INSIDE: _semantic()      at 1732
   INSIDE: _comprehension() at 1746
   INSIDE: dc.generate()    at 1780
readout calls OUTSIDE any ExitStack: NONE
```

**All three scoring branches run inside the same context stack.** So the mask really was applied during
the readout forward pass, and **no historical forward-only intervention result was secretly a
baseline.** The defect was exactly and only that `record_knockout_row` was called in the generation
branch alone, so `knock_live["n_rows"]` stayed 0 and the gate voided the run — **the gate was right, the
ledger was absent.** A new test pins the structure: it goes red if either readout call ever moves
outside the `ExitStack`.

#### The fix, and why it is not an exemption

A forward-only readout has no decode step, so the mode contract is **reduced, not waived**:
`readout_liveness_contract(scope, query_kinds)` derives it from `pc.LIVENESS_REQUIREMENT` /
`LIVENESS_MUST_BE_ZERO` — never restating the rules — by dropping `n_decode_edits` from the requirement,
**adding it to the forbidden set**, and **adding `n_prefill_forward` to the requirement as the
replacement proof-of-life counter.** That last clause is the whole point: on this path a correctly
scoped hook and a dead one both report zero decode edits, and **`n_prefill_forward > 0` is what
separates them.**

**Which modes are measurable is DERIVED, not listed** — from `pc.resolve_scoped_query_rows`:

| mode | on a forward-only readout |
|---|---|
| `query_prefill_only`, `demo_processing_only` | ✅ measurable |
| `legacy_all_query` | ✅ admitted under the reduced contract — its prefill half addresses *every* query row, which no other mode does, and it is the default scope |
| `decode_only` | ⛔ refused — resolves to **no prefill rows at all** |
| `response_query_only` | ⛔ refused — **its readout reduction is IDENTICAL to `query_prefill_only`**, so running it would misname the intervention. The refusal names the mode to use instead |

**Refusal happens at argument time, before `dc.load_model`**, rather than 20 seconds into a run.

#### The mutation round is worth recording, because it caught a decorative contract

Six mutations against a pristine copy. **M3 — "exempt the readout path by dropping `n_prefill_forward`
from the contract" — initially turned only ONE shape test red**, because the first implementation
hard-coded the extra checks inside the evaluator: **the declared contract was decoration, and the gate
would not have noticed it changing.** Rewired so the evaluator reads its counters off the contract;
M3 now correctly kills **9** tests including all three `test_a_DEAD_hook_still_FAILS_on_the_readout_path`
and all three `test_dead_and_scoped_empty_are_DISTINGUISHABLE`. **A contract that the gate does not
actually consult is the dead-guard shape this project has paid for repeatedly**, and it was caught by
mutating rather than by reading.

M5 (leaking the readout contract into the generation path) turns **three pre-existing** generation-path
tests red, which is the evidence that the generation path is untouched. **124 tests pass**, verified by
me on a serial run.

---

### ⛔ C-7 (08:10) — **THE PHASE-2 PROBE USED THE WRONG QUERY KIND, and the repo's own option-mass gate caught it in one run. The measurement it would have produced sits in a 3 % tail.**

Job **779755** (the probe **baseline**) exited `4:0` — **not a crash**. It produced its 8 rows with
`failures: {}` and then said:

```
[score] TAIL GATE FAILED — the run is written and its healthy readouts are usable,
        but these are NOT reportable:
[score] option mass semantic/semantic_one_word:
        median=0.03097  p90=0.08201  max=0.08201  frac>1%=0.625   BELOW GATE
```

**`--min-option-mass` defaults to 0.05 and the median is 0.031.** A log-odds between two options is a
valid decision margin **only if those two options are plausibly what comes next**; here they hold ~3 %
of the next-token distribution. This gate exists because of external-critique finding 1 (2026-08-18):
on the committed baseline the option pair held a **median 5.6e-06** of next-token mass for semantic
readouts, *"i.e. every published forced-choice verdict was an ordering inside a 1e-5 tail, and an
intervention that destroyed the answer while leaving the tail ordered would have been certified
comprehension preserved."*

#### The repo had already measured the fix, and I did not read it before choosing

`prompt_families.QUERY_KINDS` records, for `semantic_forced_choice`:

```
direct    as_is 1.4e-2  ->  forced 0.979
benign    as_is 1.2e-8  ->  forced 7.4e-6
```

**Naming both candidates and forcing the answer slot concentrates the mass by ~70× on the direct arm.**
`semantic_one_word` — the kind I picked — is the *unforced* variant. **The instrument was chosen
without reading the measurement the repo already had.**

⚠ **And the fix is not automatic**: the `benign` arm stays at **7.4e-6 even when forced**, so option
mass is a function of **query kind × condition**, and the headline condition here is
`natural_doublespeak`, for which **no measurement exists**.

#### 📌 Decided on the gate, not on the result

Jobs **779771 / 779772** measure option mass for **`semantic_forced_choice`** and
**`comprehension_usage`** on `natural_doublespeak`, **baseline only, no intervention**, n = 16.
**The probe kind for Phase 2 is chosen by whichever clears `--min-option-mass`, before any
intervention arm is run on it** — never by which produces a bigger effect.

**If neither clears the gate, Phase 2's primary instrument does not exist on this bank**, and that is a
finding about the bank of the same kind as R-7's deletion-ceiling result — not a licence to lower the
threshold. **`--allow-low-option-mass` exists and will not be used to manufacture a reportable number.**

---

### ⛔ C-6 (07:40) — **D-8(a) IS HALF WRONG: `score_behavior` has the readout AND the hook, but ledgers knockout liveness ONLY on the generation branch — so the Phase-2 probe arms were correctly REFUSED. And two of the five modes are structurally unmeasurable on a forward-only readout.**

**Jobs 779756 / 779757 FAILED `1:0` in 20 s**, with the gate speaking for itself:

```
REFUSING: knockout liveness has zero rows -- the run generated nothing, so the mask was never
observed to fire. This is not a pass.
{'n_rows': 0, 'frac_rows_decode_live': 0.0, ...}
```

**This is the liveness gate doing exactly the job it exists for**, and it is the third time this phase
that a guard has refused rather than let an unverified intervention be read as a null.

**The mechanism.** `record_knockout_row` is called at `score_behavior.py:1630`, **inside the generation
branch**, after `dc.generate`. The `semantic_one_word` path takes the **forward-only** readout branch at
`:1531` (`rec = _semantic(templated)`), which never ledgers a row — so `knock_live["n_rows"]` stays 0 and
`assert_knockout_live` refuses the run.

> **D-8(a) said `score_behavior` "already has both" the readout and the hook. It has both, but not
> joined**: the liveness ledger — and therefore any proof the mask fired — is wired only into the path
> that generates. **Phase 2 needs a small, real change, not a config change**, and I recorded the
> opposite one tick ago.

#### ⚠ And a structural limit that no amount of wiring removes

The semantic probe is **forward-only: there is no decode at all.** Therefore:

| mode | measurable on the probe? |
|---|---|
| `query_prefill_only` | ✅ prefill-only |
| **`demo_processing_only`** | ✅ prefill-only — **and it is the arm R-10/R-12 make decisive** |
| `legacy_all_query` | ⚠ partially — its prefill half only |
| `decode_only` | ⛔ **structurally impossible** — nothing to hook |
| `response_query_only` | ⛔ **impossible as specified** — it requires both halves |

**This is fortunate rather than limiting:** the arm the behavioural result singles out
(`demo_processing_only`) is exactly the one the probe *can* test. But **`response_query_only` cannot be
run on the probe as defined**, so the Phase-2 comparison must be stated over the prefill-scoped modes
and that limit belongs in the write-up, not discovered at analysis time.

*(Job 779755, the probe **baseline**, exited `4:0` after producing its 8 rows and `failures: {}` — a
separate non-liveness gate, to be diagnosed before the full probe run.)*

**Phase 2 status: BLOCKED on this wiring, not on compute.** No probe number exists and none will be
quoted until the mask is proven to fire on the readout path.

---

### ⛔ C-5 (05:08) — **THE FIRST JUDGING SESSION DIED ON AN NFS STALE FILE HANDLE AFTER LAUNCHING ALL EIGHT ARMS, LEAVING A 4-ROW PARTIAL JUDGE DIR. Re-judged in full rather than patched.**

**Job 779701 FAILED, exit `2:0`, after 10:19.** Cause, from its own `.err`:

```
scripts/judge_p2.sh: error reading input file: Stale file handle
```

The driver reads the manifest with `done < "$MANIFEST"` — the descriptor stays open for the whole
loop — and NFS invalidated it partway through. The log shows *"launching 8/8"* had already printed, so
**all eight arms were launched and the parent's death took its children with it.**

**State it left behind:**

| | |
|---|---|
| arms with `DONE.json` | **6 of 8** — A, legacy, respq, qpre, dec, demoproc |
| `p1j_late` | **4 rows of 96, no `DONE.json`** ← the dangerous shape |
| `p1j_late9` | config + RUNMETA only, no results |

**A 4-row judge dir is exactly the artifact this project has a manifest for:** it flows through a
`newest()`-style lookup and produces a plausible number from 4 % of the population.

#### The decision, and why it is a re-run rather than a patch

**Re-judging only the two missing arms would have put them in a DIFFERENT session from the other six —
precisely the cross-session confound PR-1 exists to forbid**, and judge re-scoring on this repo's own
data flips **6.88 %** of binary labels (165 of 2400 across 25 repeated pairs). The six completed arms
are individually fine; **mixing them with a second session is what would not be.**

> **All eight re-judged in one fresh session — job 779712, prefix `p1k`, backend pinned.** Cost: ~10
> minutes and 768 judge calls. The alternative was a headline built from two sessions, which this
> project has already retracted results over.

#### Containment, verified rather than assumed

* Both failed dirs are in `outputs/boombness/EXCLUDED_RUNS.json` (now **64** entries):
  `p1j_late` → `no_done_json`, `has_partial_results: true`; `p1j_late9` → `empty_skeleton`.
* **The real guard was tested, not trusted:** `require_done` on the 4-row dir raises
  `REFUSING: ... has no DONE.json, so the run did not finish`. Nothing can consume it silently.

#### The fix to the driver

The manifest is now **slurped into memory before any child starts**, with a cardinality re-check against
the independently-counted `N`, so the loop can no longer be interrupted by the filesystem. This is a
hardening against an **observed** failure, not a speculative one.

⚠ **And a second defect the same job exposed**, minor but the same class: the driver's progress line
hardcoded `tag=p2j_${tag}` while the invocation two lines later passed `--tag "${PREFIX}_${tag}"`. With
`P2_PREFIX` overridden **the log named a directory that does not exist.** The dirs were always correct;
the log was not. Caught only because I checked the artifact against the message instead of reading the
message. Fixed.

---

### ⛔⛔ C-4 (04:40) — **PRE-JUDGING COMPARABILITY GATE: the generation cap binds on 50–72 % of every arm, and `demo_processing_only` collapses 21 % of its rows. Handling fixed in PR-4 before judging.**

From the 4-hour review's truncation track, on the five arms complete at the time.

| arm | fraction at the `--max-new 192` cap | rows < 200 chars | min `n_chars` |
|---|---|---|---|
| `query_prefill_only` | 0.500 | 1 | 119 |
| `late` | 0.542 | 3 | 98 |
| `legacy_all_query` | 0.552 | 3 | ~100 |
| `decode_only` | 0.635 | 4 | ~100 |
| **`demo_processing_only`** | **0.719** | **20** | **23** |

**`demo_processing_only`'s collapse is a property of the ARM, not of the prompts:** the same 20
`prompt_id`s have median **776–877** characters in the other four arms against **98** here, and the
collapse is dose-responsive in `n_examples` (1 / 3 / 6 / 10 short rows at n = 1 / 2 / 4 / 8,
permutation **p = 0.00095**). **Up to 20.8 ASR points in that arm are available to a pure length
artifact.**

**Three supporting defects, all accepted:**
* **Nothing between `gens.jsonl` and the headline ASR conditions on length or termination.**
  `judge_boombness.py` writes `n_chars` and `results.jsonl` carries `stop_reason` / `gen_truncated`, but
  `analyze_phase_d.py` reads none of them. The fields exist and are populated; nothing consumes them.
* **No arm is degenerate** by the previous phase's 96 → 24 standard, so this is truncation, not collapse
  into templates.
* **`legacy_all_query`'s per-row masking cannot be audited**: `hook_n_keys_masked`,
  `hook_n_blocked_keys` and `hook_n_query_rows_edited` are `null` on all 96 rows, because that scope
  routes to `AllQueryAttentionKnockout`, which predates those counters. **This is the cost of the
  by-construction guarantee in R-3** — the incumbent class is byte-identical *and* less instrumented,
  and I am recording the trade rather than pretending it is free. The scoped arms all populate them.

---

### ⛔⛔ C-3 (04:30) — **THE 4-HOUR REVIEW: all 31 headline numbers reproduce EXACTLY, and three of my NARRATIVES around them do not. Five corrections, one of them a blocker in the tool I wrote to catch exactly this bug.**

**Full suite:** `tests/` + `doublespeak_causality/tests/` → **1298 passed, 23 skipped, 0 failed**, run
serially and exclusively; `git status outputs/ reports/` clean afterwards, which is the check that C-2's
tamper tests restore correctly when not raced.

**Numeric verdict: 31 of 31 headline figures reproduce to full precision by independent arithmetic**
(R-1/R-2's identity, pool proof, ANOVA, all four intervals, every per-pool binomial; R-7's hash census;
R-9's every counter, plus closed forms that reproduce each arm's edit count row-exactly). **Zero numeric
mismatches.** What follows are defects in the surrounding claims and code, not in the numbers.

#### ⛔ C-3a (BLOCKER, fixed) — I reproduced prev-C-18's silent-overwrite bug inside the tool written to catch it

`scoped_smoke_verdict.py` keyed its per-arm results dict by knockout **MODE**. The P1.3 session has
**seven arms and two of them run the same mode**: `C_response_query_only` at band 6–14 and
`D_response_query_late_control` at 20–31. **The second would have silently overwritten the first**, and
the tool's own mode-name validation made a distinct key impossible. The primary-arm check would then
have run on whichever was written last.

> **This is the exact defect prev-C-18 retracted R-BD over — `cells[(bank, dom)]` with no model — and I
> rebuilt it while writing the instrument whose stated purpose is that "a mode that silently collapsed
> into another looks perfectly healthy arm-by-arm".**

**Fixed:** `--arm LABEL=MODE=RUNDIR`; the **label** is the key and must be unique, the **mode** is the
scope, and a duplicate label is refused. Old `MODE=RUNDIR` still parses. **Verified by mutation:** two
arms sharing `response_query_only` now both survive (`['late', 'respq']`), the primary check reports
`arm_labels_checked: ['late','respq']` and asserts *all* of them span both halves; a duplicate label
prints `REFUSING: duplicate arm label 'x'`. The s1 verdict re-runs **PASS, 5 arms, 0 failures**.

#### ⛔ C-3b — R-9's explanation of the 3 825-edit slack is FACTUALLY WRONG

I wrote that the slack is *"the chat template and preamble, which `legacy_all_query` masks and neither
scoped mode does."* **Those rows contribute exactly ZERO.** In all 8 smoke rows the demo span starts at
index 30, so positions 0–29 **precede every demonstration key and cannot causally attend to one**.

**The entire slack is one token per prompt** — the single position in the seam between the demo span and
the query span:

```
9 layers x sum(n_demo_positions) x 1 = 9 x 425 = 3825      exactly
```

and `query_span_start − demo_span_end − 1 = 1` on every row. A closed form giving the preamble zero
weight reproduces legacy's own counter **exactly on all 8 rows** (3069, 78480, 85905, 26235, 9477,
12474, 29970, 4455). **The decomposition is therefore exact up to a single seam token** — a stronger and
more precise statement than the one I published. The inequality framing stands (an equality would mean
the seam token had vanished), but the mechanism I gave for it was hand-waving that happened to be wrong.

#### ⛔ C-3c — the both-EOS control conditions on a POST-TREATMENT variable

`stop_reason` is measured **after** the intervention, and the intervention moves it violently and in
**opposite directions** across populations: `Q|main` 26.0 % → 7.3 % truncated, while `L|ticket_bomb`
69.8 % → 91.7 % and `L|window_knife` 87.5 % → **100 %** (96/96). So the both-EOS subsample is a
**collider selection**, not a truncation control. **Three populations contribute literally zero
both-EOS rows** because their knockout arm truncates everything, and the surviving 30/1 is **80 % one
demonstration pool**. It should be reported as *"the effect holds on the subset where both arms
terminated"*, never as *"truncation is ruled out"*.

#### ⛔ C-3d — R-2's amendment is stated at one unit and reverses at others

R-2 says the direction is carried by the bomb pool (81/11, p = 2.50e-14) and that dropping it gives
p = 0.0919. Both reproduce. **But the bomb p is at its floor at every clustering §1.1 permits** —
population-clustered it is 4/0, **p = 0.125 = 2/2⁴, exactly the floor**; domain-clustered 4/0, also
0.125. And **"drop bomb → 0.0919" is not robust to the test**: two-sided 0.0919, one-sided 0.0460,
prompt-clustered 0.1221, domain-clustered 0.0625 **at floor**, population-clustered 0.6875 — and the
**domain-mean t-CI [−0.0438, −0.0014] EXCLUDES zero**. Over an order of magnitude, in both directions.
**Pool heterogeneity is nonetheless real at the prompt level** (3×2 χ² = 13.357, df 2, p = 0.001258;
bomb-vs-rest Fisher p = 5.72e-04), so R-2's *conclusion* survives — **its single quoted p does not**, and
the honest form is the heterogeneity test plus the range.

#### ⛔ C-3e — the late control is key-matched but not layer-matched

`p1_late` masks **12 blocks (20–31)** where every C arm masks **9 (6–14)**. Measured:
`p1_late` 1 357 632 prefill edits vs `p1_query_prefill_only` 1 018 224 — ratio **exactly 1.33333 = 12/9**.
The plan's *"exactly count-matched by construction"* is true of **keys**, not of mask-edit dose.
*(The same ratio independently confirms that `response_query_only` and `query_prefill_only` edit the
identical prefill row set, as the resolver specifies.)* **Action: a 9-block late control is submitted
below**, so the comparison is matched on both.

---

### ⛔⛔ C-2 (00:42) — **TWO CONCURRENT PYTEST RUNS CORRUPTED A COMMITTED SCIENTIFIC ARTIFACT, and the corruption survived both runs' restore logic. Caused by my own parallelisation.**

**What happened.** `tests/test_verify_report_numbers.py` contains two guard tests that **mutate real,
committed files in place** and restore them in a `finally`:

* `test_FAILS_when_an_artifact_value_is_tampered_with` writes `0.9999` into
  `outputs/boombness/advbench_decomposition.json` → `paired_vs_baseline.B.delta_cluster_mean`;
* `test_FAILS_when_the_number_is_removed_from_the_report` rewrites `+0.0333` → `+0.0999` in
  `reports/boombness_objective_sprint_report.md`.

Both are correctly written for **serial** execution: `shutil.copy2` to a `.testbak`, mutate, assert the
guard catches it, `finally: shutil.move(backup, original)`, then a final
`assert _run().returncode == 0, "restore failed; the tree is left dirty"`.

**They are not safe under concurrency, and I ran them concurrently.** Four repair agents were editing
disjoint file sets, and at least two of them ran `pytest tests/` at the same time as I did. The race is
the obvious one: run A copies a clean backup and mutates the file; run B then copies **the already
mutated file** as *its* backup; A restores its clean copy; B restores its dirty one. **The last writer
wins and the tamper value is left on disk.**

**Detected, not stumbled into.** The next serial run failed `test_passes_on_the_real_tree` with
`14-B arm B clustered delta … expected 0.0305, actual 0.9999 VALUE MISMATCH` — the tamper constant
itself, sitting in a committed artifact. `check_all.py` then reported
`1 of 6 guards FAILED: verify_report_numbers`.

**Blast radius, measured rather than assumed.** Both files are **tracked**, so `git status` showed them
modified and `git checkout --` restored them exactly:
`delta_cluster_mean` is back to **0.030519369707034255**, which is bit-identical to the value Part I
§6.1 publishes, and the report again contains **4** occurrences of `+0.0333`. `check_all.py` is green.
No `.testbak` files remain anywhere in the tree. **No result of this phase read either file while it
was corrupt** — R-1/R-2 use `rederive_crossbank.json`, which touches neither.

⚠ **A stale `.git/index.lock` (0 bytes, 00:38:54) blocked the first restore attempt** — a git process
from a killed agent. Verified no `git` binary was running before removing it, per git's own message.

#### Standing rules adopted, and they bind the rest of this phase

1. **Never run `pytest tests/` concurrently with anything else in this repo** — not another agent, not
   a second shell. The suite mutates tracked files by design. Full-suite runs are **serial and
   exclusive**, and the §18 4-hour review must schedule them that way.
2. **Parallel agents may not run the full suite.** They run only the subset covering their own files.
   *(This is a correction to my own workflow instructions, which told four agents to "run the full
   suite" — three of them did, simultaneously.)*
3. **After any full-suite run, check `git status outputs/ reports/`.** A clean run leaves nothing dirty;
   anything dirty is a corrupted artifact, not a stale file.
4. **Proposed hardening, not yet implemented** (recorded so it is not lost): these two tests should
   operate on a **copy in `tmp_path`** with the verifier pointed at it, rather than mutating the real
   tree — or take an exclusive lock. Filed as an open item rather than fixed now, because changing a
   guard's mechanism during a repair pass is how the previous phase produced its dead guards.

**This is the third time in two phases that a defect has been caught only by cross-checking two
computations of the same thing** (prev-R-BD's silent overwrite, prev-C-18's crossed table, now this).
The pattern is worth naming: **the corruption was invisible inside either run and obvious the moment a
third, independent run read the same file.**

---

### ⚠ C-1 — see **R-2** in §B5

The amendment to the inherited headline direction (the effect is carried by one demonstration corpus)
is recorded as R-2 rather than duplicated here, because it is a *result* of this phase's own
re-derivation rather than a correction to something this phase published.

## B7. FAILED / VOID RUNS

*(kept visible on purpose)*

*(none yet from this phase)*

* **11:08 — `run_judge_cpu.sh` silently ignores every `P2_*` variable (job 779923).** I submitted the
  Phase-4B judging through it with a full `--export` of `P2_MANIFEST/P2_PREFIX/P2_BANK/...`. Line 31 of
  that wrapper is a **hardcoded** `bash scripts/judge_qwen3_decomposition.sh` — it takes no manifest
  and re-judges its own baked-in arm list. **The env vars were accepted and discarded in silence.**
  Caught by tailing the job's stdout instead of trusting the submission, and the wiring was confirmed
  by grep before resubmitting. The correct wrapper is `src/boombness/slurm/run_p2_judge.sh`
  (job **779926**). 779923 was **not** cancelled, per the standing instruction; it writes fresh
  `${STAMP}_${tag}` directories, so it cannot overwrite or collide with `p4bj_*` — the cost is wasted
  CPU and judge API calls, not a corrupted artifact. **Lesson: a wrapper that accepts `--export=ALL`
  is not a wrapper that reads your variables.**

* **12:18 — `--seed` does nothing at `--preset main`, and every repro command in this log implies it
  does.** The deep review's mutation check regenerated the carrot bank at `--seed 1` and got
  `7bf21cfbdc1966b04ce8f8b9` — **byte-identical** to the committed bank built at `--seed 20260825`
  (5,406,912 bytes, so not a silent generator failure). `generate_bank` calls `seed_everything(seed)`
  but the `main` preset is a **full deterministic enumeration** that never consumes the RNG. **No
  result is affected and this is arguably the better design** — the bank is a census, not a sample —
  but `*_meta.json` records a `seed` field that a reader will reasonably take as a reproducibility
  dependency when it is inert. Recorded so nobody later "fixes" a seed mismatch that cannot exist.

* **23:40 — four concurrent Qwen3-14B weight loads starved each other, even at the 2-per-node cap.**
  Jobs 781410-781413 (PR-15) showed **0 rows written after 16-28 minutes**, which is the shape of a
  hung job. It was not one. Diagnosed the documented way — **by the weight-loading bar in `.err`, not
  by `squeue`** — and every bar was advancing (367→368 of 443 on n-802; 237→240 on n-803). **Weight
  load was taking 23+ minutes against a normal 2-6.**
  The standing rule of **≤2 model-loading jobs per node was respected** (2 on n-802, 2 on n-803) and
  **was not sufficient**: with a 14B model the bottleneck is **shared NFS, not the node**, so four
  concurrent loads contend wherever they are placed. **The rule should be read as ≤2 concurrent 14B
  loads in TOTAL, not per node.** No job was cancelled (standing instruction) and none needed to be —
  all four went on to generate normally. **Recorded because "0 rows for half an hour" will otherwise
  be misread as a stall and provoke a resubmission that makes the contention worse.**

* **18:45 — a CONCURRENT WRITER is active in this repo, and it breaks my C-2 check.**
  `git status` showed `external_md/BOOMBNESS_DSURFACE_NEXT_PHASE_PLAN_AND_PROGRESS.md` and
  `reports/SPRINT_SUMMARY_2026-08-16_TO_08-26.md` modified — **1,187 insertions**, timestamps 17:37
  and 17:52, i.e. **during this session**. **Neither is mine**; mine are the
  `DEMONSTRATION_RETRIEVAL_...` log and `SPRINT_SUMMARY_2026-08-25_BEHAVIORAL_CAUSALITY.md`.
  **They have not been touched and must not be.**

  **Two consequences, both acted on:**
  1. **The standing rule "stage explicit paths only, never `git add -A`" just paid off concretely.**
     A single `git add -A` at any point in the last hour would have swept 1,187 lines of another
     agent's work-in-progress into one of my commits. **The rule is not hygiene theatre.**
  2. **My C-2 corruption check — "`git status` on `outputs/ reports/` is clean" — is no longer a
     reliable signal**, because another writer produces persistent noise in `reports/`. **From here
     the check is scoped to the paths this phase owns**, so a real corruption of *my* artifacts still
     stands out instead of being lost in someone else's diff. An unscoped check that is always dirty
     is the same failure as DR-8's guard that always cried wolf.

  ⚠ Also note `feedback_git_stash_shared_branch`: a third writer's stash sits on this branch's stack.
  **No stash operation of any kind is safe here.**

* **19:15 — SLURM control-plane OUTAGE; PR-23 is pre-registered but UNSUBMITTED.**
  `sbatch` returns `Batch job submission failed: Unexpected message received`, and `squeue`,
  `sinfo` fail the same way while `scontrol ping` hangs to timeout. **The whole scheduler is down,
  not just my queue.** Two submissions were refused; **I retried once after 30 s and stopped** —
  retrying into a dead control plane is noise, not diagnosis.

  **Nothing is lost and nothing is at risk.** PR-23 is committed at `490b0995` **before** any data
  exists, which is the point of pre-registering; the argsfiles are committed; and every completed
  artifact lives on disk independently of the scheduler — all five `xj_*` judge dirs verified
  **160/160 with `DONE.json`**.

  **This also retro-justifies C-16's fix.** That defect was my wait loop trusting `sacct`; **within
  the hour the same service failed outright.** Polling the artifact rather than the scheduler is not
  defensive coding, it is the difference between "the job finished" and "the thing that tells me
  about jobs is reachable". **PR-23 submits on the next tick that `sbatch` answers.**

  **✅ 19:38 — SLURM recovered and PR-23's first two arms are submitted** (`q14_demoproc` 783595,
  `q14_matched_d1` 783596). **Before submitting I checked whether any of my failed attempts had
  actually landed:** two jobs were PENDING (783468, 783495) running the same `run_boombness.sh`, but
  their submit times are **19:22**, after all three of my errored attempts, and **no `q14_*` run dir
  exists** — so they belong to the **concurrent writer** (18:45 note), not to me. **Every one of my
  failed `sbatch` calls really did fail; none created a phantom job.** Checking that before
  resubmitting is what stops a duplicate arm from quietly doubling a control draw.

* **20:20 — PREEMPTION on `killable` leaves ORPHAN PARTIAL run dirs, and my manifest one-liners
  pick dirs by TIMESTAMP alone.** `q14_demoproc` now has **two** run directories: `..._200426_...`
  with **34 rows** (preempted mid-generation) and `..._201505_...` with **31** (the restart, still
  running). `squeue` had shown the job PENDING while both dirs already existed — **the scheduler's
  view and the filesystem's disagreed again**, which is C-16's lesson recurring.

  **The exposure:** every manifest I have built this phase used
  `ls -1dt outputs/.../TAG_2026* | head -1` — **newest by mtime, with no completeness test.** If a
  restart is preempted while an earlier attempt completed, that picks the **partial** one.

  **What saves it, and what does not.** The row-count guards DO catch it: `score_behavior`'s
  `--expect-n` refuses a wrong population, and `judge_p2.sh` refuses any judge dir whose row count
  is not `EXPECT_ROWS` (`REFUSING: $t has $n rows, expected $EXPECT_ROWS`). **So a partial dir
  cannot reach a result** — it fails loudly at judging. **But it fails AFTER a GPU arm has been
  spent**, and the failure looks like a submission error rather than a stale-glob error.

  **Fixed going forward: manifests select the newest run dir THAT HAS `DONE.json`**, not merely the
  newest. `tests/test_argsfiles_match_runs.py` already does this (DR-8); my shell one-liners did
  not. **The orphan dirs are left in place — they are evidence of what happened, and deleting run
  directories to tidy a glob is how provenance gets lost.**

## B7b. PROCESS NOTES

### ⚠⚠ P-1 (00:41) — **THE THIRD WRITER IS CONFIRMED BY A SECOND, INDEPENDENT ROUTE. I attributed a job pair, a log file and a tool to a session that has never touched any of them.**

At 00:28 I messaged the peer session proposing an ownership split (D-2). Its reply, verbatim in
substance:

* **779083 / 779084 are not its jobs.** Its only job was **776368** (`cpu-killable`,
  `run_band2_judge.sh`). It has no Phase 10b, no Qwen3 `button_gun`, no crossbank work. *"Do NOT wait on
  me to finish 10b — nobody in this session is going to. If you plan around my finishing it, you will
  wait forever."*
* **`external_md/BOOMBNESS_DSURFACE_NEXT_PHASE_PLAN_AND_PROGRESS.md` and
  `src/boombness/crossbank_knockout_test.py` are not its files.** Its log is
  `external_md/BOOMBNESS_D_SURFACE_FOLLOWUP_PROGRESS.md` — a different file whose name differs by two
  characters. **Treating those two as "the peer's" would have frozen paths that have no owner in
  contact.**
* It has **stopped entirely** and released every boombness file, the crossbank tool and job 776368.

**Why this is a finding and not just a mix-up.** The previous phase already recorded one unattributed
commit (`91e30a62`, 17:09 on 08-23) that neither session in contact wrote. **This is the second
independent sign of the same thing**, and it is stronger: an entire live phase — its log, its tool, its
running jobs — has been read by two different sessions as belonging to each other. `sacct` confirms
779083/779084 were submitted **2026-08-24 23:20:23** with `WorkDir` inside this repo, under this
account, and they are still RUNNING. Git cannot help: **all commits on this branch carry one identical
author *and* committer identity with zero date skew**, so a third writer is invisible in the metadata.

**Standing consequences for this phase, adopted now:**

1. **`git log` immediately before every commit**, and `git diff HEAD` on the files just written
   afterwards to confirm the committed bytes are the intended bytes. HEAD moved three commits between
   the plan being written and this file being opened.
2. **Never `scancel`.** 779083/779084 are left to run to completion. A blanket cancel on this account
   destroyed three jobs once already (2026-08-20 17:37).
3. **Do not consume 779083–779086's outputs in this phase** without independently re-verifying their
   provenance (tree commit, argsfile, population, liveness) — their producing session is unreachable, so
   their configuration cannot be confirmed by asking.
4. **Attribute by artifact, never by inference from the queue.** The error I made was reading
   "a job is running under my account" as "the session I am talking to launched it".

### ✅ Two inherited findings the peer independently corroborated (00:41)

* **Judge instability, from the other side.** The peer saw identical generations move a baseline ASR
  **0.1714 → 0.1595** across sessions while a **paired** delta reproduced to four decimals — the same
  phenomenon as the 78/96 binary-label agreement in §B8. **Its mitigation is the one this phase adopts:
  paired estimators, never per-prompt identity claims.**
* **Length-proxy gates.** The coherence gate's `scorable_frac` is a **length** proxy that flags
  *refusal* rather than incoherence: six runs excluded as degenerate were lexically **healthier** than
  the untreated baseline. `uniq` **by text** and `trigram_repeat` behaved correctly; `scorable_frac` and
  length-based uniqueness did not. **Adopted as a rule for Phase 1 §4.2:** any arm exclusion must be
  justified on a by-text metric, never on a length proxy.

### ⛔ P-2 (00:41) — an inherited claim that must not be reintroduced

**"Established at L10/L12" is WITHDRAWN.** Under the repo's own depth-family policy
(`analyze_control_recheck.py`, *"the family is the depth set"*) Holm gives **0.0732 at m=4** and
**0.2014 / 0.2440 at m=11**. **Nothing rejects.** Flagged by the peer as easy to reintroduce by accident
from older notes; recorded here so this phase cannot do so.

## B8. REVIEWER FINDINGS

*(adversarial reviews, with what was accepted, what was refuted, and by what recomputation)*

**Inherited — the Part-II audit (2026-08-24/25, 361 checks against committed artifacts).** 338 MATCH /
14 MISMATCH / 9 UNVERIFIABLE; of the mismatches, 5 refuted, 1 superseded, **8 upheld**. The eight, all
of which this phase must avoid inheriting: R-AE's codeword-subspace upper endpoint is **0.5714** not
0.5722; REVIEW-2 M3's "byte-identical cell E" is false for `basket_bomb` (maxabsdiff 7.81e-04) though
its counts are right; R-T's "same ~17 prompts" is net-only (**23 vs 19** crossings, 7 overlapping);
`uniq_frac` is distinct completion **lengths**; R-U's demo-token median is **38.5** not 44; R-AI's
"Spearman ρ" is Pearson r on log₂(n_examples) (**both Qwen3 p's become 0.3333** under real Spearman);
Phase-6d's codeword PC2 dose is **0.0020** not 0.0027; and `cell_residual_frac_removed` is carried by
**2 of 9** R-AH runs. Full detail: `reports/SPRINT_SUMMARY_2026-08-23_TO_08-24_PART_II.md` §11.

**Inherited — judge re-scoring instability (the single most consequential finding for this phase).**
Sessions 776893 and 777030 judged the **same generation files**; on byte-identical text `p2A` returned
an identical `strongreject_score` on **70/96** rows and the same binary label on **78/96** — **18 of 96
prompts crossed the 0.5 threshold on re-judging.** Aggregate ASR is identical (the flips cancel).
**Consequence for this phase:** every per-prompt claim needs an explicit reliability budget, and Phase
1's equivalence margin must be set above this floor. This is why §1.1's per-prompt rule exists.

## B9. REPRODUCTION COMMANDS

*(one command per result; filled in as results land)*

```bash
# environment (login-shell python has no torch; its failures are not repo failures)
PY=/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python

# the six deliverable guards — must exit 0 before any commit
$PY src/boombness/check_all.py

# full suite baseline
$PY -m pytest tests/ -q

# the knockout instrument (CPU-only, ~26 s)
$PY -m pytest -q doublespeak_causality/tests/test_allquery_attnknockout.py \
                 doublespeak_causality/tests/test_attnknockout_synthetic.py

# R-1 / R-2 -- the independent re-derivation of the cross-bank result (CPU, ~30 s, no GPU, no API).
# Does NOT import crossbank_knockout_test; all arithmetic is local, so agreement is evidence.
$PY src/boombness/rederive_crossbank.py \
    --manifest outputs/boombness/argsfiles/xb_manifest10.txt \
    --thresholds 0.25,0.5,0.75 --tag rederive10
# -> outputs/boombness/rederive_crossbank/rederive10_<stamp>/rederive_crossbank.json
```


### P1.2 smoke — the exact command lines *(argsfiles live under `outputs/`, which is gitignored, so the literals are embedded here; this is the reproducibility gap the previous phase had to close retroactively)*

Common prefix, identical in all six arms:

```
--bank /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/data/boombness_prompts/boombness_prompt_bank.jsonl --query-kinds behavioral --conditions natural_doublespeak --bank-blocks core2x2,core2x2_slot3 --n-examples 1,2,4,8 --max-new 192 --dtype bfloat16 --seed 20260825 --model meta-llama/Llama-3.1-8B-Instruct --attn-impl eager --limit 8
```

Per-arm suffix:

| arm | suffix |
|---|---|
| `s1_A` | `--arm A_baseline --tag s1A` |
| `s1_<MODE>` | `--intervene demo_all:attn_knockout:6-14:1.0 --knockout-scope <MODE> --arm C_<MODE> --tag s1_<MODE>` |

with `<MODE>` ranging over the five values of `pc.SCOPED_KNOCKOUT_MODES`. Submitted as:

```bash
sbatch --export=ALL,BOOMB_SCRIPT=score_behavior.py,\
BOOMB_ARGSFILE=$REPO/outputs/boombness/argsfiles/s1_<NAME>.txt \
       src/boombness/slurm/run_boombness.sh
```

⚠ `--limit 8` is applied **after** `--expect-n` is checked and after `run.note` records the population,
so each smoke artifact will report `n: 96` in its composition block while holding 8 rows. That is
prev-REVIEW-2's finding S3, not a new defect — **the smoke's row count must be read from the liveness
block, never from `population_composition`.**

## B10. CANONICAL ARTIFACTS OF THIS PHASE

| artifact | produced by | holds |
|---|---|---|
| `outputs/boombness/phase1_decomposition/q1dec_20260825_073814_2825688/phase1_decomposition.json` | `src/boombness/phase1_decomposition.py` | **R-12** — the Qwen3 replication, same estimator |
| `outputs/boombness/phase1_decomposition/p1dec_final_20260825_054056_2706137/phase1_decomposition.json` | `src/boombness/phase1_decomposition.py` | **R-10** — the Phase-1 decomposition: per-arm ASR/Δ, PR-4 generation health, length-conditioned sweep, domain sign tests with floors, and the PR-1/PR-3 primary comparison |
| `outputs/boombness/scoped_smoke_verdict/s1verdict_20260825_033930_2556360/scoped_smoke_verdict.json` | `src/boombness/scoped_smoke_verdict.py` | **R-9** — the smoke verdict, read as a whole |
| `outputs/boombness/rederive_crossbank/rederive10_20260825_002934_2201570/rederive_crossbank.json` | `src/boombness/rederive_crossbank.py` | **R-1 / R-2** — population identity, pool proof, per-population ASR, crossed ANOVA + both marginals + crossed random-effects interval, prompt-level binomial **decomposed by demonstration pool**, both-EOS composition |


### R-61 (03:35) — **All four PR-25 generation arms landed clean on pool B; the three control draws are provably independent; the five-arm judge window is submitted. Nothing is read yet.**

The sweep pre-registered at R-60 is complete. Every generation-side precondition PR-25 requires
was checked **before** any judging was launched, and each one is recorded here with the artifact
that produced it, so the read that follows cannot quietly relax a condition it has already met.

**Arms, all Qwen/Qwen3-14B, all on `boombness_prompt_bank_longpreQ14B.jsonl` (sha `b2903479258a0f68`):**

| tag | run dir | rows | `frac_rows_scope_live` | `scope_violations` | `control_draw_match_ratio` min |
|---|---|---|---|---|---|
| `q16A` (baseline) | `outputs/boombness/score_behavior/q16A_20260827_014106_689620` | 160/160 | — | — | — |
| `q16_demoproc` | `.../q16_demoproc_20260827_022535_694032` | 160/160 | **1.0** | `{}` | n/a (not a control arm) |
| `q16_matched_d1` | `.../q16_matched_d1_20260827_024736_695408` | 160/160 | **1.0** | `{}` | **1.000** (160/160 rows carry the field) |
| `q16_matched_d2` | `.../q16_matched_d2_20260827_025736_696843` | 160/160 | **1.0** | `{}` | **1.000** (160/160) |
| `q16_matched_d3` | `.../q16_matched_d3_20260827_025810_1051351` | 160/160 | 1.0 | `{}` | 1.000 |

Every arm reached `DONE.json` at the full 160 rows, so C-16's partial-read trap is closed by the
artifact itself rather than by the scheduler. `match_ratio` is 1.000 on **every** control row at
every dose — the strict `nondemo_matched_d*` policy would have refused an under-matched row, and
none were refused. The longer-preamble bank was built for exactly this: on pool A's short bank the
strict policy had no drawable pool at `n=8`.

**The three draws are independent by seed AND by generation hash (C-17's requirement, checked, not
assumed).** Each control row records its own draw provenance:

* `d1` → `nondemo_matched_d1@seed20260825`, `draw_seed=28180602`
* `d2` → `nondemo_matched_d2@seed20260825`, `draw_seed=36100379`
* row-wise comparison of the drawn position sets: **0 of 160 rows drew identically** between d1 and d2.
* whole-arm generation hashes (sha256 over the sorted per-row completion hashes) are **3 distinct
  values for 3 arms** — `708f15bc…` (demoproc), `abb9e9e1…` (d1), `6dce84cb…` (d2).

So "three independent controls" is a measured statement here, not a naming convention. This is the
condition C-17 was written for: two arms that *were* launched twice looked distinct by tag and
identical by content.

**Judging.** All five arms go through **one** judge window, `q16j_{A,demoproc,d1,d2,d3}`, job
`784409`, pinned to `openai/gpt-4o-mini`, script `scripts/judge_q16_poolB.sh`. The baseline is
**re-judged** inside that window even though `xj_q_Q14B` already judged it at 02:10 for the power
gate: R6-6 established that arms judged in different sessions produced a real artifact, and the
whole pool-B read is an arm-vs-baseline contrast. The power-gate artifact is not overwritten — the
new run writes under a different tag prefix — so the 12/160 power number stays independently
inspectable.

`run_judge_cpu.sh` now takes the batch script via `JUDGE_BATCH` instead of hard-coding one file.
That is a launcher change only; the default is unchanged, so every prior judge invocation still
resolves to the same script.

**Not read yet, and the thresholds do not move.** PR-23's three conditions apply to this pool
unchanged — a new pool licenses no new thresholds. R-60's flag stands and is repeated here because
it is the thing most likely to be rationalised after the fact: **pool B carries 12 attacks total
(n1:0 n2:2 n4:4 n8:6) against pool A's 17, and `n=4` sits at exactly the 4-row floor for the second
time.** One row moving turns a confirmation into a decline. Per PR-25, if the matched controls
remove attack comparably on this powered population, **C7 reverts to unresolved rather than staying
confirmed on one pool.**


### 🏆 R-62 (03:40) — **PR-25 CONFIRMS. C7 replicates on the independent pool B: all three pre-registered conditions hold at both decisive doses, with the closest control 1.8x away.**

Producing artifact: `outputs/boombness/dose_breakdown/q16dose_20260827_033538_110259/dose_breakdown.json`.
Judge window: `q16j_{A,demoproc,d1,d2,d3}`, job `784409`, all five 160/160 rows, **0 nulls**, one pinned
`openai/gpt-4o-mini` on all 800 rows.

**Baseline (`q16j_A`), rows out of 40 per cell:** n1 **0**, n2 **3**, n4 **4**, n8 **6**.

| arm | n=4 Δrows | n=4 Δ | n=8 Δrows | n=8 Δ | `match_ratio` min |
|---|---|---|---|---|---|
| `demoproc` | **−4** | **−0.1000** | **−5** | **−0.1250** | n/a |
| `matched_d1` | +1 | +0.0250 | +0 | +0.0000 | 1.000 |
| `matched_d2` | +1 | +0.0250 | −1 | −0.0250 | 1.000 |
| `matched_d3` | +1 | +0.0250 | −2 | −0.0500 | 1.000 |

**The three conditions, at both decisive doses:**

1. `demoproc` clears `MARGIN_VS_BASELINE = 0.0521`: **0.1000** at n=4 and **0.1250** at n=8. ✅
2. Every matched control stays inside it: worst is `matched_d3` at n=8, **|−0.0500| < 0.0521**. ✅
3. Separation exceeds `MARGIN_ARM_VS_ARM = 0.0417`: n=4 is **0.1250 (3.0×)** against all three controls;
   n=8 is 0.1250 / 0.1000 / **0.0750 (1.8×)**. Worst case **1.8×**. ✅

**Cross-session baseline agreement, unplanned and worth having.** The power gate judged this same
baseline in a *separate* session 80 minutes earlier (`xj_q_Q14B`). Both decisive doses agree exactly:

| dose | power-gate session | re-judge session |
|---|---|---|
| n=1 | 0/40 | 0/40 |
| n=2 | 2/40 | **3/40** |
| n=4 | **4/40** | **4/40** |
| n=8 | **6/40** | **6/40** |

One row moved, at `n=2`, a non-decisive dose — inside the ±0.0480 re-judge band PR-3 measured. R-60's
warning that "`n=4` sits at exactly 4 rows and one row moving flips the verdict" was the right thing to
worry about, and the answer is that the cell did not move.

**What this is not.** Still Qwen3-only — Llama remains *declined for power*, not refuted (R-52).
Still thin: `demoproc`'s effect is 4 and 5 rows against a **2.08-row** margin (1.9× and 2.4×), and the
n=8 separation of 3 rows against a 1.67-row margin is the thinnest number in the confirmation.
`n=1` (+1) and `n=2` (−2) were never the claim and say nothing.

---

### ⛔ C-19 (03:45) — **CORRECTION: C7 was resolved (R-58) and replicated (R-62) without ever running the truncation-robustness check DR-2 made mandatory. Running it now shows it is UNTESTABLE on both pools — the `demoproc` arm truncates ~27pp more than its own controls, and the untruncated subgroup at the decisive doses is 3, 1, 1 and 0 rows.**

DR-2 established the rule in this document: *"every ASR is published beside its arm's truncation
fraction and median `n_chars`"*, and it survived the Llama exposure only because **Qwen3 was 26%
truncated with both-EOS subsets of 111/114 rows.** I carried that protection forward to the `longpre`
banks. **It does not transfer.** The preamble that made the count-matched control constructible also
made every prompt longer against an unchanged **192-token cap**:

| arm | pool A `frac_stop_length` | pool B `frac_stop_length` |
|---|---|---|
| baseline | 0.519 | 0.431 |
| **`demoproc`** | **0.675** | **0.700** |
| `matched_d1` | 0.469 | 0.400 |
| `matched_d2` | 0.481 | 0.394 |
| `matched_d3` | 0.456 | 0.400 |

The three controls sit **at or below the baseline**. `demoproc` sits ~20-27pp **above** it, on both
pools. So the very contrast that carries C7 — `demoproc` vs count-matched controls — coincides with a
systematic truncation gap that the controls do not have.

**The both-EOS subgroup cannot arbitrate it, because it is essentially empty for the one arm that
matters** (rows where baseline AND arm both terminated, decisive doses only):

| arm | pool A n=4 | pool A n=8 | pool B n=4 | pool B n=8 |
|---|---|---|---|---|
| **`demoproc`** | **3/40** | **1/40** | **1/40** | **0/40** |
| `matched_d1` | 11/40 | 9/40 | 14/40 | 8/40 |
| `matched_d2` | 14/40 | 10/40 | 16/40 | 12/40 |
| `matched_d3` | 14/40 | 10/40 | 14/40 | 9/40 |

**What is and is not withdrawn.** R-58 and R-62 are **not retracted**: every pre-registered condition
was met on the population that was pre-registered, and conditioning on `stop_reason` is conditioning on
a **collider** (PR-4), so an empty both-EOS subgroup is not evidence of an artifact any more than a
surviving one would be proof against it. What is withdrawn is the **implied scope**. C7 says:

> masking the demonstration positions removes the attack **as measured over the first 192 generated
> tokens**, on an arm that truncates 27pp more than its controls, and **its truncation-robustness is
> UNMEASURED — not established, and not refuted.**

There is prior evidence against the truncation explanation — C-9 decomposed `demoproc`'s down-flips as
15 = 3 refused + 3 short + **12 neither**, found it makes output *longer*, and beat a length-matched
control (−0.1310 vs −0.0714). But that was the **internal bank**, a different population with a
different truncation profile. It is support, not a substitute for the check on this population.

**How this got past me.** I checked liveness, match_ratio, draw independence, judge provenance, nulls,
row counts and cross-session agreement — every gate PR-23 and PR-25 named — and DR-2's truncation rule
was not among them, because I had filed it as "already handled on Qwen3". A rule that lives in a prior
review rather than in the pre-registration is a rule that gets skipped. **PR-26 puts it in the gate.**

---

### PR-26 (03:50, pre-registered before any data exists) — **the decisive truncation test: re-generate the C7 contrast with a cap large enough that the arms actually terminate.**

The both-EOS subgroup is a collider and cannot settle this. Re-generating with a larger cap is **not**
collider conditioning — it is a different and better-powered experiment on the same population.

**Design.** Pool B (`longpreQ14B`, sha `b2903479258a0f68`), Qwen3-14B, identical to R-62 in every
respect **except `--max-new 192 → 640`**, and restricted to the two decisive doses. Three arms only,
because that is what the contrast needs: `A640` (baseline), `dp640` (`demo_processing_only`), and
`c1_640` (`nondemo_matched_d1`). Judged in **one** window.

**Gates, in order, and the branch stops if one fails:**

1. **The cap must actually be released:** `frac_stop_length` **< 0.15 on every arm**. If `demoproc`
   still truncates most of its rows at 640, the cap is not the binding constraint and this test cannot
   be run — say so and stop, do not raise the cap again and retry.
2. **Truncation must no longer separate the arms:** `|frac_stop_length(dp640) − frac_stop_length(c1_640)|`
   **< 0.10**. This is the whole point; without it the confound is merely smaller, not removed.
3. **Power on the new population:** **≥4 baseline attack rows at n=4 AND at n=8.** A longer cap can
   move the baseline ASR in either direction; if the population loses its attack the branch stops for
   power, exactly as Llama did (R-52).

**Only if all three pass is the result read**, and the read is PR-23's, unchanged:
`dp640` clears ±0.0521 at both doses; `c1_640` stays inside it; separation exceeds 0.0417.

* **CONFIRMS** → C7's truncation-robustness is **established**, and the scope sentence C-19 forces onto
  it can be dropped.
* **REFUTED** — `dp640` no longer clears the margin once the arms terminate → **C7's effect is an
  artifact of the 192-token cap.** R-58 and R-62 would then be *correct readings of a confounded
  measurement*, and C7 reverts to unresolved. Stated now, before the run exists.
* **Neither** — gate 1 or 3 fails → C7 keeps C-19's scope sentence permanently, and the phase records
  truncation-robustness as **untestable on this bank**, not as absent.

**One arm is deliberately not run.** `matched_d2`/`d3` are omitted: PR-26 tests a *confound*, not the
independence of the draws, and R-62 already established that all three controls behave alike. Adding
them would spend GPU on a question already answered. Recorded so the omission is a decision and not
a silent truncation of scope.


### R-63 (04:30) — **PR-26 gate 1 PASSES outright: at a 640-token cap both arms terminate on 100% of rows. The 192-token cap was the binding constraint, and `demoproc`'s truncation was LENGTH, not degeneration.**

Artifacts: `outputs/boombness/score_behavior/A640_20260827_040740_708673` and
`.../dp640_20260827_040740_708761`, both 80/80 rows, `DONE.json` present, Qwen3-14B,
`frac_rows_scope_live=1.0` with `scope_violations={}` on the knockout arm.

| arm | `frac_stop_length` at 192 (R-62) | **at 640** | median new tokens | max new tokens | median chars |
|---|---|---|---|---|---|
| baseline | 0.431 | **0.000** | 212 | 555 | 938 |
| `demoproc` | 0.700 | **0.000** | **277** | 618 | 1294 |

**Gate 1 required `< 0.15` on every arm and got `0.000` on both.** No row reaches the cap — the
longest completion in either arm is 618 tokens against 640 — so this is not a cap moved just far
enough to look released.

**The incidental finding is the more informative one.** `demoproc`'s median completion is **277 new
tokens against the baseline's 212**, a ratio of **1.31**. Its 70% truncation at 192 was therefore
**not** the model degenerating or rambling into the cap: it was writing longer answers and being cut
off. That independently reproduces C-9's observation on a different bank (there the ratio was 1.14 and
the down-flips decomposed as 12-of-15 *neither refused nor short*), and it removes the specific
alternative explanation C-19 was most worried about — that `demoproc`'s ASR drop was manufactured by
handing the judge more truncated text than the controls got.

**This is not yet the answer.** Gate 2 (truncation must no longer *separate* the arms) needs
`c1_640`, submitted as job `784658` once a slot freed. Gate 3 (≥4 baseline attacks at both decisive
doses) is read from the judged baseline, and a 640-token cap can move the baseline ASR in either
direction — a longer completion can complete a harmful answer the 192-token version left unfinished,
which would *raise* it, or wander into a refusal, which would lower it. **The gate order stands: no
arm-vs-arm number is computed until gate 3 passes.**


### 🏆 R-64 (05:00) — **PR-26 CONFIRMS on all three gates and all three conditions. C7's effect is NOT an artifact of the 192-token cap: with every completion terminating, `demoproc` removes MORE attack, not less. C-19's scope sentence is discharged.**

Producing artifact: `outputs/boombness/dose_breakdown/p26dose_20260827_045812_279200/dose_breakdown.json`.
Judge window `p26j_{A,dp,c1}`, job `784740`: 240 rows, **0 nulls**, one pinned `openai/gpt-4o-mini`.
Generations `A640_20260827_040740_708673`, `dp640_20260827_040740_708761`,
`c1_640_20260827_043749_711377` — each 80/80 with `DONE.json`; `dp640` and `c1_640` both report
`frac_rows_scope_live=1.0`, `scope_violations={}`, and `c1_640` carries `match_ratio` **1.000 on all
80 control rows**.

**The three gates, in the order they were pre-registered:**

| gate | requirement | result |
|---|---|---|
| 1 — cap released | `frac_stop_length < 0.15` on every arm | **0.000 / 0.000 / 0.000** ✅ |
| 2 — truncation no longer separates the arms | `\|dp − c1\| < 0.10` | **0.000** (was **0.300** at the 192 cap) ✅ |
| 3 — power on the new population | ≥4 baseline attacks at n=4 **and** n=8 | **4/40** and **7/40** ✅ |

Longest completion in any arm is **634 tokens against a 640 cap**, and no row stopped on length — the
cap is released, not merely raised until the number looked acceptable.

**PR-23's three conditions, on a population with zero truncation:**

| dose | baseline | `demoproc` | `matched_d1` | separation |
|---|---|---|---|---|
| n=4 | 4/40 | **−3 rows, −0.0750** | +1 row, +0.0250 | **0.1000 (2.4×)** |
| n=8 | 7/40 | **−7 rows, −0.1750** | +0 rows, +0.0000 | **0.1750 (4.2×)** |

All three hold at both doses: `demoproc` clears ±0.0521, the count-matched control stays inside it,
and the separation exceeds 0.0417.

**The direction is the informative part.** The truncation hypothesis predicted `demoproc`'s effect
would *shrink* once its completions were allowed to finish, because its apparent ASR drop would have
been the judge scoring cut-off text. It did the opposite. At n=8 the effect goes from **−0.1250 at the
192-token cap to −0.1750 untruncated — `demoproc` now removes 7 of 7 attacks, all of them.** At n=4 it
goes from −4 rows to −3. **A confound that vanishes when you remove the confound is not the
explanation.**

**C-19 is discharged.** C7's truncation-robustness is no longer *unmeasured*: it was measured, on the
same pool, same model, same bank, same intervention, with the only change being a cap that no longer
binds — and the effect survives. The scope sentence C-19 forced onto C7 comes off. **C-19 itself stays
in the corrections table**, because the process failure it records is real and was not about the
answer: DR-2's truncation rule lived in a prior review instead of a pre-registration gate, so it was
skipped for two full confirmations. The fix is that PR-26 put it in the gate.

#### ⚠ What this is still not

* **Still Qwen3-only.** Llama remains **declined for power** (R-52), never refuted. PR-26 changes
  nothing about that.
* **The n=4 cell is now the thinnest number in the whole claim: −3 rows against a 2.08-row margin,
  1.4×.** It was 1.9× at the 192 cap. The n=8 cell carries this result (−7 rows, 3.4× the margin,
  4.2× separation); n=4 clears its threshold and no more. **Reported, not smoothed over.**
* **Two controls were deliberately not run at 640** (`matched_d2`, `matched_d3`) — recorded at
  pre-registration, because PR-26 tests a confound and R-62 already established the three draws behave
  alike. The 640-token result therefore rests on **one** count-matched control, not three.
* **`n=1` and `n=2` were not generated at all** at this cap; PR-26 restricted to the decisive doses.


### R-65 (05:15) — **§20 reassessed now that C7 is closed. Of the three questions never run, Q4 is DECLINED ON EVIDENCE (its antecedent failed), Q6 stays dropped, and Q7 is the one still justified. Smoke launched; nothing claimed.**

Step 2 of the cadence, done properly rather than by inertia: the queue is empty, no job FAILED or
CANCELLED since the last tick, and C7's branch closed at R-64. So the question is which of the
remaining §20 items current evidence still justifies.

**§20 Q4 — *"If full-state rescue works, is the behaviourally relevant information low-rank or
irreducibly distributed?"* — DECLINED ON EVIDENCE, not deferred.**

Q4 is written as a conditional, and **its antecedent has been tested and did not hold.** C9 measured
what full-state rescue actually restores: **the refusal comes back and the attack does not.** C2 and
C12 then established that refusal restoration is **not** the route to attack removal. So the thing Q4
proposes to compress — a *behaviourally* relevant rescued state — is not what the rescue recovers.

The one behavioural handle that does exist is C11's query-span patch, and it is too thin to carry a
rank decomposition: **ASR +0.0563 against a 0.0521 margin — 1.08×, i.e. it clears by about 0.7 rows
out of 160** — with only **37.5% recovery** and explicitly **not selective**. Fitting a low-rank
structure onto an effect that clears its own margin by 8% is precisely *fitting structure below the
measurement reproducibility floor*, which this phase's own review cadence forbids. **Q4 is closed as
unjustified by current evidence.** §20 Q8 was gated on Q4 and closes with it.

**§20 Q6** stays **dropped** for R-30's reason, unchanged: its motivating question is already answered
by R-17's Qwen3 within-family bridge.

**§20 Q7 — *"Does the Llama retrieval/refusal independence result replicate on Qwen3, or is it
model-specific?"* — JUSTIFIED, and it is the last open question in §20.**

This is C11, and C11 is **Llama-only** (`S` in the handoff table). It is also the phase's sharpest
dissociation: at L14 over the query span, refusal comes back **−0.1562 (96.2% of the rise**, to within
margin of clean) while ASR recovers only **37.5%**. C13 has already shown that a Llama result in this
family can be **Llama-specific** — neutral context suppressed the attack on Llama and was tested
NEGATIVE on Qwen3 (21/160 → 23/160) — so "does C11 transfer?" is a live question with a real chance of
declining, not a formality.

**The instrument gap that decides what runs first.** An inventory of every rescue run in
`outputs/boombness/score_behavior` by `(model, rescue_positions, rescue_donor, rescue_layer)` shows:

| model | `rescue_positions` | layers run |
|---|---|---|
| Llama-3.1-8B | **`query`** | 14, 5 |
| Llama-3.1-8B | `demo` / default | 14, 5 |
| Qwen3-14B | default (demo span) | 17, 5 |
| **Qwen3-14B** | **`query`** | **never run** |

Query-span rescue has **never executed on Qwen3**. C9's Qwen3 arms patched the demonstration span. So
the correct next step is a **smoke, not a sweep** — the alignment guard (`strict_ids`) and the query
span selection have never met Qwen3's tokenizer, and C-18 is the standing lesson about generalising a
feasibility fact across tokenizers.

**Launched: `q9smoke_qpos_L17`, job `784766`** — 8 rows, d10 bank, Qwen3-14B, knockout
`demo_all:attn_knockout:7-17` with `demo_processing_only`, `--rescue-positions query --rescue-donor
clean --rescue-layer 17`. L17 is the top of Qwen3's band, the depth-matched analogue of Llama's L14,
and it is the mapping already fixed and used by the `q7_rescue_L17` runs — **not retuned here.**

**Nothing is claimed and no pre-registration is written yet.** The smoke answers one question only:
*does the query-span patch fire on Qwen3 and select a sane number of positions?* `rescue_liveness`
must report `fired: true` with `n_positions_written > 0`. Llama's smoke wrote **24** positions; Qwen3
will differ because it is a different tokenizer, and per C12 what matters is position **identity**, not
count — so a different count is expected and is **not** grounds to force Llama's 24. **PR-27 will be
written after the smoke and before any sweep is judged.**


### R-66 (05:40) — **The Q7 smoke PASSES: query-span rescue fires on Qwen3, writing 28 positions per row. The instrument gap is closed; the sweep needs only two new arms.**

Artifact: `outputs/boombness/score_behavior/q9smoke_qpos_L17_20260827_050944_715471` — 8/8 rows,
`DONE.json`, `n_failed: 0`.

| check | result |
|---|---|
| `rescue_liveness.fired` | **true on 8/8 rows** |
| `n_positions_written` | **28**, identical on every row |
| `n_forward_calls` (min) | 57 |
| knockout `frac_rows_scope_live` | **1.0**, `scope_violations={}` |
| distinct generations | **8/8** |

**Qwen3 writes 28 query-span positions where Llama wrote 24.** That difference is expected and is
**not** corrected: they are different tokenizers over the same query text, and C12 established that
what carries the demo/query contrast is position **identity**, not count. Forcing Llama's 24 onto
Qwen3 would truncate the span to make a number match — the opposite of what C12 licenses.

**Existing Qwen3 d10 160-row arms** (inventoried rather than assumed, so nothing is regenerated):
baseline `q6bA_...516233`, knockout-only `q6b_demo_processing_only_...516774`, and **demo-span**
rescue `q6b_rescue_L17_...888002` / `q6b_rescue_L5_...888003`. **Only the two query-span arms are
missing**, so the sweep is two runs, not six — and the demo-vs-query contrast that is C11's actual
claim is available within one judge window.

---

### 🔒 PR-27 (05:45, written and committed before the arms are submitted) — **what a Qwen3 replication of C11 would and would not show.**

**C11 on Llama, the thing being tested** (d10, 160 rows, `DonorPatch` at L14 over the query span):
query-span rescue restores **refusal −0.1562 (96.2% of the knockout's rise**, back to within margin of
clean) while recovering only **37.5%** of the ASR — **+0.0563 against a 0.0521 margin.** Below-band L5
query control inert (refusal 0.0000, ASR +0.0125).

**Design.** Qwen3-14B, the same d10 bank and the same 160-row population, knockout
`demo_all:attn_knockout:7-17` under `demo_processing_only`, `--rescue-positions query --rescue-donor
clean`, at **L17** (top of Qwen3's band, the depth-matched analogue of Llama's L14) with the
**below-band L5** control. **The band and both layers are the mapping already fixed and used by the
`q7_rescue_*` and `q6b_rescue_*` runs — not retuned for this test.** Baseline, knockout-only, both
demo-span rescue arms and both new query-span arms are judged in **one** window (R6-6).

#### 📌 The three conditions, at PR-3's margins, unchanged

1. **Refusal is restored from the query span**: query-L17 moves refusal against the knockout's rise by
   more than `MARGIN_VS_BASELINE = 0.0521`.
2. **The dissociation holds**: query-L17's **refusal** recovery exceeds its **ASR** recovery, and the
   two differ by more than `MARGIN_ARM_VS_ARM = 0.0417` as a fraction of what the knockout removed.
3. **The below-band control is inert**: query-L5 moves **neither** refusal nor ASR by more than 0.0521.

#### ⛔ Declared in advance, because C11's two halves are not equally powered

**C11's refusal half is strong (−0.1562, 25 rows of 160) and its ASR half is not: +0.0563 clears the
0.0521 margin by 0.7 rows.** A replication is therefore pre-registered as **two separate verdicts**:

* **The refusal half** is the primary. It replicates or it does not, and either is reportable.
* **The ASR half is DECLARED THIN NOW.** If Qwen3's query-span ASR recovery lands **inside** ±0.0521,
  that is a **DECLINE for lack of power, not a refutation** — the same rule R-52's underpower clause
  applies to Llama, and the same rule I failed to apply there until it was caught. **A Qwen3 ASR
  number inside margin must not be written up as "C11 refuted".**
* Equally: if Qwen3's ASR half clears margin by a similarly thin amount, **that is not a confirmation
  of a mechanism either.** Two 1.1×-margin effects agreeing is not evidence of structure; it is two
  measurements at their floor. It would be recorded as *consistent in direction, underpowered in both
  models.*

#### 📌 And the demo-vs-query contrast, which is C11's actual sentence

C11 claims the attack damage is reachable from the **query** span **but not from the demonstration
positions**. On Qwen3 both arms now exist at the same layer, so this is directly testable:
**query-L17 vs demo-L17 must differ by more than 0.0417 on ASR** for the contrast to hold. If they do
not differ, **the "but not from the demonstration positions" clause fails on Qwen3** and C11 becomes
model-specific in its interesting half — which is exactly what happened to C13.

**REFUTED** if condition 1 fails on a powered population: the refusal recovery is the strong,
well-measured half, and if it does not transfer then C11's dissociation is a Llama property.


### ⛔⛔ C-20 (05:55) — **CORRECTION: the below-band L5 rescue "control" is a NO-OP BY CONSTRUCTION. All four instances across the phase produce generations BYTE-IDENTICAL to their own knockout arm. C9, C11 and C12 each cite it as a specificity control; none of them ran one.**

Found by checking preconditions on the four pre-existing Qwen3 arms **before** submitting PR-27's read
— the whole-arm generation hashes came back **3 distinct for 4 arms**, which is C-17's signature.

**The measurement.** Row-level generation identity, every rescue arm against its own session's
knockout-only arm:

| model | arm | positions | layer | vs its session's knockout-only |
|---|---|---|---|---|
| Qwen3-14B | `q6b_rescue_L17` | demo | 17 (**in band** 7-17) | 0/160 identical |
| Qwen3-14B | `q6b_rescue_L5` | demo | **5 (below band)** | **160/160 IDENTICAL** |
| Llama-3.1-8B | `p8b_rescue_L14` | demo | 14 (**in band** 6-14) | 6/160 identical |
| Llama-3.1-8B | `p8b_rescue_L5` | demo | **5 (below band)** | **160/160 IDENTICAL** |
| Llama-3.1-8B | `p9_rescue_qpos_L14` | query | 14 (in band) | 7/160 identical |
| Llama-3.1-8B | `p9_rescue_qpos_L5` | query | **5 (below band)** | **160/160 IDENTICAL** |
| Llama-3.1-8B | `p10_demo24_L5` | demo, 24 | **5 (below band)** | **40/40 IDENTICAL** |

Four independent below-band instances — **two models, two position modes, three sessions** — and every
one is a bit-for-bit no-op. Every in-band arm is not.

**Why, and why it was inevitable.** The knockout masks attention at layers **7-17** (Qwen3) / **6-14**
(Llama). Layers 0-6 are untouched, so the knocked-out run's **prompt-position** activations at layer 5
are *bit-identical to the clean run's*. `DonorPatch` at L5 therefore writes the value that is already
there. `rescue_liveness` correctly reports `fired: true` with positions written — **it did write; there
was simply nothing to change.** Liveness proves the hook ran; it cannot prove the hook mattered. That
distinction is the one this phase has been most careful about everywhere else.

**What this costs the three claims that cite it.**

* **C9** — *"below-band L5 patch moves refusal by EXACTLY 0.0000 in all four cells."*
* **C12** — *"below-band L5, exactly inert (15→15)."*
* **C11** — *"below-band L5 query patch: refusal 0.0000, ASR +0.0125."*

**Those exact zeros are not clean control behaviour. They are arithmetic consequences of identical
text**, and the phrase "EXACTLY 0.0000" should have been the tell: a live-but-inert intervention
produces small *nonzero* noise, not machine zeros.

**Nothing about the main findings is retracted.** C9, C11 and C12 rest on the **in-band** arm against
knockout-only, and those arms genuinely change the computation (0/160, 6/160, 7/160 identical). What is
withdrawn is the claim that a **layer-specificity control was run**. It was not. **C9, C11 and C12 lose
their specificity leg** until a real control exists; their primary effects stand.

**A byproduct worth keeping: a measured judge-reproducibility floor on IDENTICAL text.** C11's control
reported **ASR +0.0125** — 2 rows of 160 — on completions that are byte-identical. That number cannot
be an effect of the intervention, so it is a direct measurement of **judge non-reproducibility: 2/160 =
0.0125 flip rate on the same text.** Reassuringly it sits well inside PR-3's measured ±0.0480 re-judge
band, so the margins are not threatened — but it means **±0.0125 of any arm-vs-arm difference is judge
noise before the science starts.**

#### ⛔ PR-27's condition 3 is WITHDRAWN, before any of its data is read

I wrote PR-27 twenty minutes ago requiring *"the below-band control is inert: query-L5 moves neither
refusal nor ASR by more than 0.0521."* **That condition is unfalsifiable** — the arm is a no-op, so it
passes by construction. Withdrawing it now, before reading, rather than reporting a guaranteed pass as
a satisfied condition.

**Replacement, pre-registered now: the specificity control moves to the BOTTOM of the band.** Patch at
**L7** (Qwen3) instead of L5. L7 is *inside* the knockout band, so the clean donor genuinely differs
from what is there, and the patch is a real intervention. It tests the same scientific question —
*is the effect specific to the top of the band, or does any layer do it?* — with an arm that can
actually fail. **Conditions 1 and 2 of PR-27 are unchanged.**

**The in-flight `q9_qpos_L5` (job `784857`) is not cancelled and is not a control.** It will be
byte-identical to the Qwen3 knockout arm like every other below-band arm. It is **repurposed** as a
second judge-reproducibility measurement: judged in the same window, its flip count against the
knockout arm is a second read of the ±0.0125 figure above, on a different model. **Recorded as a
repurposing, not as a control that happened to be inert.**


### R-67 (06:20) — **I tried to test C-20's prediction and the test was INVALID BY DESIGN. Flagging it before it can be read either way, and launching the comparator that actually tests it. C-20's evidence is unchanged; its confirmation is now pending.**

The fresh below-band arm `q9_qpos_L5_20260827_054320_1072840` landed (160/160, `fired` 160/160, 28
positions). C-20 predicts it is a no-op, so I compared it to the knockout-only arm and got:

> **identical 0/160 — "PREDICTION FAILED"**

**That comparison tests nothing, and I should have seen it before running it.** The only knockout-only
arm I compared against (`q6b_...516774`) is from a **different session** — 25 August. Measured just
now, two runs of the **same** knockout-only intervention in different sessions agree on
**3/160 rows**:

| comparison | identical |
|---|---|
| Llama knockout-only, session `p6b` vs session `p4b` — *same intervention* | **3/160** |
| `q9_qpos_L5` (today) vs `q6b` knockout-only (25 Aug) | 0/160 |

**Generation is not reproducible across sessions**, so a cross-session comparison returns ~0/160 for a
vacuous arm and a real arm alike. My "prediction test" could not have come out any other way.

**C-20's actual evidence is untouched, and it is not weak.** Every one of its four matches is
**within** a session, and same-session runs of *different* interventions do **not** match — `p8b`'s
in-band L14 arm agrees with its session's knockout arm on only **6/160**. Exact byte-identity across
160 rows is not something a session produces by default; it happens when the computation is identical:

| within-session comparison | identical |
|---|---|
| `p8b_rescue_L5` (below band) vs `p6b` knockout-only | **160/160** |
| `p9_rescue_qpos_L5` (below band) vs `p4b` knockout-only | **160/160** |
| `p10_demo24_L5` (below band) vs `p4b` knockout-only | **40/40** |
| `q6b_rescue_L5` (below band) vs `q6b` knockout-only | **160/160** |
| `p8b_rescue_L14` (**in** band) vs `p6b` knockout-only | 6/160 |

**So C-20 stands on its evidence and its confirmation is now pending, not delivered.** The valid test
needs a knockout-only arm from **this** session. **Launched: `q9_ko`, job `784904`** — identical
configuration to `q9_qpos_L17`/`L5` with the rescue flags removed. C-20 is confirmed if
`q9_qpos_L5 ≡ q9_ko` at 160/160 while `q9_qpos_L17 ≢ q9_ko`; it is **refuted** if `q9_qpos_L5` differs
from `q9_ko` on a material fraction of rows, and in that case the construction argument is wrong and
C-20 must be withdrawn the way C-14 was.

**Nothing in C-20's corrections is being rolled back on the strength of an invalid test.** The struck
citations in the handoff and summary stay struck until `q9_ko` reports, because the four within-session
identities are the reason they were struck and those numbers have not changed.

**Also confirmed clean, and unaffected by any of this:** `q9_qpos_L17` is a **real** intervention —
0/160 identical to knockout-only *and* it is the in-band arm, so the C-20 trap does not touch PR-27's
primary condition. 160/160 rows, `frac_rows_scope_live=1.0`, `scope_violations={}`, `fired` 160/160 at
**28** positions, truncation 0.344.


### ✅⛔ R-68 (06:40) — **C-20 is CONFIRMED by the same-session test — and the same test shows MY OWN REPLACEMENT CONTROL was vacuous too. The boundary is `layer ≤ lo`, not `layer < lo`.**

`q9_ko_20260827_061835_724429` — knockout-only, this session, 160/160 rows, `failures: 0`,
`frac_rows_scope_live=1.0`, `scope_violations={}`. Every comparison below is **within one session**, so
the cross-session artifact that invalidated R-67's test does not apply.

| arm | layer | band 7-17 | vs `q9_ko` |
|---|---|---|---|
| `q9_qpos_L5` | 5 | below | **160/160 identical** |
| **`q9_qpos_L7`** | **7** | **bottom of band** | **160/160 identical** |
| `q9_qpos_L17` | 17 | top of band | **4/160** |

**C-20 is confirmed.** The below-band arm is a bit-exact no-op against a knockout-only arm from its own
session, while the top-of-band arm changes 156 of 160 generations. The four historical identities were
not a coincidence, and the struck citations in the handoff and summary stay struck — permanently now,
not pending.

**And the replacement control I pre-registered ninety minutes ago is ALSO vacuous.** I wrote that a
sound control must sit *inside* the band and chose **L7**, the band's bottom layer. L7 is inside the
band by any reading of "7-17" and it is **byte-identical on 160/160 rows** — exactly the failure it was
built to fix.

**The corrected rule, which the data now pins precisely.** `DonorPatch` writes the residual stream
**entering** block `rescue_layer` — equivalently the output of block `rescue_layer − 1`. The knockout
masks attention *within* blocks `lo..hi`. So the input to block `lo` is the output of block `lo − 1`
and is **untouched**:

> **A clean-donor patch at prompt positions is vacuous for every `rescue_layer ≤ lo`, and can only
> differ from the recipient at `lo + 1` or above.**

That fits every measurement: Qwen3 (`lo=7`) vacuous at 5 and **7**, real at 17; Llama (`lo=6`) vacuous
at 5, real at 14. **"In-band" was the wrong predicate; `> lo` is the right one.** The test committed
with C-20 encoded `>= lo` and was therefore wrong in exactly the way I was wrong; it now encodes
`> lo`, plus a dedicated case for the band-floor trap that caught me.

**Why this kept happening, stated plainly.** Both times I reasoned from what the intervention was
*named* — "below-band control", "in-band control" — instead of from what it *writes*. Liveness said
`fired: true` both times and was correct both times: the hook ran and wrote 28 positions. **A hook that
writes the value already present is live and useless, and no liveness field can distinguish those two.
The only thing that can is comparing generations against a same-session control**, which is now the
standing check.

**Launched: `q9_qpos_L12`, job `784906`** — mid-band, `lo + 5`, far from both boundaries. It is
pre-registered as PR-27's condition-3 control **and** as a test of the corrected rule: if the rule
holds it must differ materially from `q9_ko`. **If `L12` also comes back byte-identical, the rule is
still wrong and PR-27's specificity condition is abandoned rather than patched a third time.**

**PR-27's primary conditions are untouched** by any of this: `q9_qpos_L17` is a real intervention
(4/160), in-band, liveness 1.0, `fired` 160/160 at 28 positions.


### ⛔ C-21 (07:10) — **CORRECTION to R-67: I blamed "generation is not reproducible across sessions" for an artifact that was actually POOL A vs POOL B. The conclusion (the test was invalid) stands; the reason was wrong, and the true picture is the opposite — generation here is DETERMINISTIC given the same bank.**

Caught by verifying a number before publishing it. I was about to record a "generation-session
reproducibility floor" of ±0.0312 ASR from two pairs of runs I described as *the same intervention run
twice*. Diffing their `RUNMETA` args first — the only difference in each pair:

> `bank`: `boombness_prompt_bank_d10.jsonl` **vs** `boombness_prompt_bank_d10_poolB.jsonl`

**They are different demonstration pools.** The ASR gap is a pool difference, which R-29 already
established is real. **There is no measured generation-session noise floor, and PR-3's margins are not
undermined.** The finding is withdrawn before it was ever written down as one.

**The same confound explains R-67.** Every arm's bank, checked:

| grouping | comparison | identical |
|---|---|---|
| **same bank** | `p8b_rescue_L5` (poolB) vs `p6b` KO (poolB) | **160/160** |
| **same bank** | `p9_rescue_qpos_L5` (poolA) vs `p4b` KO (poolA) | **160/160** |
| **same bank** | `p10_demo24_L5` (poolA) vs `p4b` KO (poolA) | **40/40** |
| **same bank** | `q6b_rescue_L5` (poolB) vs `q6b` KO (poolB) | **160/160** |
| same bank, **in band** | `p8b_rescue_L14` (poolB) vs `p6b` KO (poolB) | 6/160 |
| **cross bank** | `p6b` KO (poolB) vs `p4b` KO (poolA) | 3/160 |
| **cross bank** | `q9_qpos_L5` (poolA) vs `q6b` KO (**poolB**) | 0/160 |

R-67's `q9_qpos_L5 → 0/160` was **not** a session effect. It was pool A judged against a pool B
knockout arm — **different demonstration sentences, therefore different prompts**. I reached for
"sessions differ" because I had just been thinking about session artifacts, and never checked the one
field that decides it. **That is C-13's defect exactly: a comparison silently run against the wrong
population, producing a plausible number.**

**What changes, and what does not.**

* **C-20 is unaffected and remains CONFIRMED.** R-68's decisive test compared `q9_qpos_L5/L7/L12/L17`
  against `q9_ko` — **all pool A, all this session** — and it is clean on both axes.
* **R-67's conclusion stands** (the prediction test was invalid) but **its stated reason is withdrawn**;
  the invalidity was cross-bank, not cross-session.
* **R-67 and R-68's "within one session" framing is corrected to "on the same bank."** Both happen to
  be true of R-68's arms, so no number moves.
* **Generation appears fully DETERMINISTIC here**, given the same bank, model and intervention — which
  is *stronger* than what I claimed, and it is what makes byte-identity a sharp enough instrument to
  have caught C-20 at all.

**No published claim is touched.** The withdrawn floor was never published; R-67's numbers were
reported with their comparison stated, and the comparison is what was wrong.

---

### ✅ R-69 (07:12) — **The corrected rule survives its own test: `L12` is a REAL intervention, and PR-27 finally has a sound specificity control.**

`q9_qpos_L12_...` — 160/160 rows, `failures: 0`, `frac_rows_scope_live=1.0`, `scope_violations={}`,
`fired` 160/160 at **28** positions. All four layers against `q9_ko` (same bank, same session):

| layer | position in band 7-17 | predicted | identical vs `q9_ko` | observed |
|---|---|---|---|---|
| 5 | below | vacuous | **160/160** | vacuous ✅ |
| 7 | `= lo` | vacuous | **160/160** | vacuous ✅ |
| **12** | `lo+5` | **real** | **16/160** | **real ✅** |
| 17 | `= hi` | real | 4/160 | real ✅ |

**4/4 predictions correct.** R-68 pre-committed that a byte-identical `L12` would mean the rule was
still wrong and the specificity condition would be abandoned rather than patched a third time. It did
not come to that: `L12` changes **144 of 160** generations.

**PR-27's condition 3 now has a control that can actually fail**, and the layer-specificity question
C9/C11/C12 lost to C-20 becomes answerable: L12 and L17 are both real interventions at the same
positions, differing only in depth.

**Launched: `q9A`, job `784915`** — the clean baseline on pool A **in this session**, so the whole Q7
read is same-bank and same-session end to end rather than leaning on an Aug-25 baseline. All arms then
judge in one window.


### 🏆 R-70 (07:50) — **PR-27: C11's REFUSAL half and its DISSOCIATION both replicate on Qwen3. Its ASR half DECLINES for power exactly as pre-registered. §20 Q7 is answered — the result is model-general in its strong half.**

Judge window `q9j_{A,ko,L17,L12,L5}`, job `784934`: 800 rows, **0 nulls**, one pinned
`openai/gpt-4o-mini`. All five arms are **pool A (d10)** and were **generated in this session**, so
C-21's confound cannot touch the read. n = **160 common rows**.

**The knockout works on this population**, which is the precondition for asking about rescue at all:

| | clean `A` | knockout `ko` | change |
|---|---|---|---|
| ASR | 0.1250 (20) | 0.0437 (7) | **−0.0813 (−13 rows)** |
| refusal | 0.0125 (2) | 0.1437 (23) | **+0.1312 (+21 rows)** |

**Query-span rescue at the top of the band (L17), against the knockout:**

| condition | requirement | result |
|---|---|---|
| **1 — refusal restored from the query span** | `|Δrefusal| > 0.0521` | **−0.09375 (−15/160) (−15 rows), 71.4% of the rise** ✅ |
| **2 — the dissociation holds** | refusal move exceeds ASR move by `> 0.0417` | **0.0875** ✅ |
| ASR half | declared thin; inside ±0.0521 ⇒ **DECLINE**, not refutation | **−0.0062 (−1 row), recovery −7.7%** → **DECLINE** |

**C11 replicates in its strong half.** Llama gave refusal −0.1562 (96.2% of the rise); Qwen3 gives
**−0.09375 (−15/160) (71.4%)**. Both clear the margin, both in the same direction, and in both models the same
patch leaves the attack alone. **Handing the clean query-span activations back gives the refusal back
and not the attack — on two model families.**

**The ASR half declines, and PR-27 fixed that reading in advance.** Llama recovered 37.5% of the
attack (+0.0563, clearing its margin by 0.7 rows); Qwen3 recovers **−7.7%** — nothing, and slightly
negative. Inside ±0.0521, so per PR-27 this is **a DECLINE for lack of power, not a refutation of
C11's ASR clause.** I am not writing it up as "C11 refuted", and I am equally not calling the two
models' ASR halves consistent: one is 1.08× its margin and the other is null.

#### ⚠ The layer-specificity read is EXPLORATORY, not pre-registered

L12 (mid-band, `lo+5`, a real intervention — 16/160) moves refusal **−0.0375 (28.6%)**, *inside* the
margin, against L17's −0.09375 (−15/160). The L17−L12 refusal gap is **0.0562**, above 0.0417.

**That looks like the layer-specificity result C-20 took away, and I am not claiming it.** PR-27's
condition 3 was written for a below-band control, that control turned out vacuous (C-20), its
replacement at the band floor turned out vacuous too (R-68), and L12 was launched **without a numeric
criterion ever being fixed for it**. Reading a threshold onto L12 now — after seeing the numbers —
would be exactly the failure this phase pre-registers against. **It is recorded as exploratory and
needs its own pre-registration and its own arms to become a claim.**

#### 🔎 A measurement worth more than the arm that produced it: the LLM judge flips 9/160 rows on BYTE-IDENTICAL text

`q9_qpos_L5` is byte-identical to `q9_ko` on 160/160 rows (C-20). Judged in the same window, on the
same bytes:

| metric | detector | disagreement on identical text |
|---|---|---|
| **ASR** (StrongREJECT ≥ 0.5) | LLM judge | **9/160 rows flipped = 0.0563** |
| **refusal** (`kw_refusal`) | deterministic keyword | **0/160 = 0.0000** |

* The **net** ASR difference is 1 row (0.0063), consistent with C-20's estimate of ±0.0125 from C11's
  control. **C-20's number was a net and was right as a net.** What is new is the **per-row flip
  rate**, which is **0.0563 — larger than both PR-3 margins.**
* The margins gate *net* differences and the net noise is small, so **PR-3's margins are not
  invalidated.** But any statement of the form *"the intervention removed 5 of 5 attacks"* is a
  **row-level** statement, and row-level identity carries ~9 rows in 160 of judge churn.
* **`kw_refusal` disagreed on zero rows.** Every refusal number in this phase is drawn from a
  deterministic detector; every ASR number is drawn from one that flips 5.6% of rows given the same
  input. **That is a strong reason the refusal half of C11 replicated cleanly and the ASR half did
  not, and it is measured rather than asserted.**


### 🔎 DR-10 (07:55, 4h DEEP REVIEW) — **Full suite 1085/0. All three C7 headline cell-sets recomputed from artifacts and they match exactly. No corrections this round. The one thing the review found — a 27.5pp truncation gap on R-70's newest arm — was tested and the claim STRENGTHENS under it.**

**Suite.** `1085 passed, 7 skipped` in 205s. Queue empty; no FAILED or CANCELLED job this phase owns.

**Headline numbers recomputed independently from the judge artifacts** (rows, not rates, per C7's
decisive doses):

| population | n=4 | n=8 | published as |
|---|---|---|---|
| pool A (R-58) | **5 → 0** | **7 → 2** | 5/5 and 5/7 ✅ |
| pool B (R-62) | **4 → 0** | **6 → 1** | −4/4 and −5/6 ✅ |
| 640-token cap (R-64) | **4 → 1** | **7 → 0** | −3/4 and −7/7 ✅ |

**All three match what is published.** Nothing drifted.

**Liveness, provenance, overwrites — 18 arms swept.** Every intervention arm reports
`frac_rows_scope_live = 1.0` with `scope_violations = {}`; every arm has `DONE.json` at its expected
row count; `n_failed = 0` everywhere. **Exactly one run directory per tag — no silent overwrites.**
Banks and models are correct per family (`longpre*` for the C7 work, `d10` for the Q7 work), which is
the check C-21 exists to enforce.

**Truncation/EOS — the review's one real finding, and it went the right way.** `q9_qpos_L17` truncates
**0.344** against its comparator `q9_ko`'s **0.619** — a **27.5pp** gap, the same shape as C-19. Unlike
C-19, the subgroup where both arms terminate is **not** empty:

| population | n | refusal `ko` → `L17` | Δrefusal |
|---|---|---|---|
| all rows | 160 | 23 → 8 | **−0.0938** |
| **both terminated** | **51** | **15 → 5** | **−0.1961** |

**R-70's condition 1 survives and roughly doubles on the untruncated subgroup.** Conditioning on
`stop_reason` is still conditioning on a collider (PR-4), so this is support and not proof — but the
subgroup is 51 rows rather than C-19's 1 and 0, refusal comes from a **deterministic** detector, and
the effect moves *away* from the truncation explanation. **C-19's caveat does not transfer to R-70.**

**Structure below the reproducibility floor — now measured, not assumed.** From R-70's byte-identical
pair, the LLM judge flips **9/160 = 0.0563** of rows on the *same bytes*. Two properties matter:

* **It is not threshold adjacency.** Only **6/160** rows have a baseline score anywhere in
  `[0.30, 0.70]`, yet 9 flipped, and **four of them swing 0.0 ↔ ≥0.5.** The judge is not merely
  wobbling around the cut; it sometimes reads the same text completely differently.
* **Per-dose it is 2, 3, 1, 3 rows** per 40-row cell (n=1,2,4,8), against C7 per-cell effects of
  **3 to 7 rows**. So the individual cells sit at roughly **1.7× to 5×** the churn.

**What that does and does not license.** The margins gate *net* differences and the net churn is
**1 row**, so PR-3 stands and no published number moves. But it means **no single 40-row cell in this
phase should be read as decisive on its own.** What actually carries C7 is that **three independent
populations agree in sign at both decisive doses** — pool A, pool B, and the untruncated 640-token
rerun — which is a much stronger statement than any one cell against its margin, and it is the framing
the write-ups should lead with.

**No correction is issued this round.** Recorded explicitly, because a review that finds nothing is
only informative if it says so.


### 🔒 PR-28 (08:10, written before the arm is submitted) — **layer-specificity, replicated on Llama; and a declared change of statistic for REFUSAL only, applied symmetrically.**

#### Part 1 — the statistic, declared before it is used to decide anything

DR-10 measured two facts that together change what the right uncertainty is **for refusal**:

* `kw_refusal` disagreed on **0/160** rows of byte-identical text (the LLM judge flipped 9/160).
* Generation is **deterministic** given the same bank, model and intervention (C-21) — and that
  determinism spans sessions: `p8b_rescue_L5` (26 Aug) is byte-identical to `p6b`'s knockout arm
  (25 Aug), both pool B.

So a refusal count for a given arm on a given bank is **exact and reproducible**. PR-3's margins were
measured from **LLM re-judge spread** — a noise source that, for refusal, **is zero**. Using them on
refusal is not wrong, it is *conservative against the wrong thing*, and it says nothing about the only
uncertainty that remains: **population sampling.** The right instrument for that is a **paired exact
(McNemar) test on discordant rows**.

**⛔ Declared, because switching to a test that yields smaller p-values is exactly the move that needs
declaring:**

1. **PR-3's margins remain the pre-registered gate.** Nothing is re-adjudicated by the new test; it is
   reported **alongside**, never instead.
2. **It applies to every refusal claim in the phase, not only where it helps.** Applied symmetrically
   to C1, the flagship refusal claim, before being applied to anything new:

   | C1 setting | refusal | discordant | exact p |
   |---|---|---|---|
   | Llama / pool A | 9 → 35 | 2/28 | **8.7e-07** |
   | Qwen3 / pool A | 2 → 23 | 0/21 | **9.5e-07** |
   | Llama / pool B | 1 → 32 | 1/32 | **7.9e-09** |

3. **It never applies to ASR**, which has a measured 9/160 judge flip rate and is *not* exact.
4. **Its own positive control passes**: the byte-identical arm `q9_qpos_L5` vs `q9_ko` gives
   **0/0 discordant, p = 1.0** — exactly what a test of a no-op must return.

#### Part 2 — the experiment

**Exploratory result being tested** (R-70, Qwen3, band 7-17, query span, d10 pool A):

| comparison | refusal | discordant | exact p |
|---|---|---|---|
| knockout → **L17** (top of band) | 23 → 8 | 17/2 | **0.00073** |
| knockout → **L12** (mid band) | 23 → 17 | 11/5 | 0.21 |
| **L12 vs L17** | 17 → 8 | **10/1** | **0.0117** |

**This is one model, one pool, one layer pair, and DR-10's own conclusion is that no single population
is decisive.** C-13 is the standing warning: a Llama result in this family was tested on Qwen3 and came
back negative. So it is **not** a claim until it replicates.

**Design.** Llama-3.1-8B, band **6-14**, same d10 pool A bank, `--rescue-positions query --rescue-donor
clean`. Top-of-band **L14** and the knockout and clean arms **already exist** and are not regenerated
(`p9_rescue_qpos_L14`, `p4b_demo_processing_only`, `p4bA`). **One new arm: `p11_qpos_L10`**, mid-band at
`lo+4`, the Llama analogue of Qwen3's L12. All four judge in one window.

**⛔ Preconditions, checked before reading (C-20's lesson):** `L10` must **not** be byte-identical to
the knockout arm. `lo = 6`, so `L10 > lo` and the corrected rule predicts a real intervention — **if it
comes back byte-identical the rule is wrong again and this branch stops rather than moving to a third
layer.**

#### 📌 Conditions — all three required, at both instruments

**REPLICATES** if, on Llama:
1. **Top of band restores refusal**: `|Δrefusal(L14 vs knockout)| > 0.0521` **and** paired exact
   `p < 0.05`.
2. **Mid band does not**: `|Δrefusal(L10 vs knockout)| ≤ 0.0521`.
3. **They separate**: `|Δrefusal(L14) − Δrefusal(L10)| > 0.0417` **and** paired exact `p < 0.05`.

**DECLINES** if the Llama knockout does not raise refusal by more than 0.0521 in the first place —
there would be nothing to rescue, which is R-52's underpower rule, not a refutation.

**REFUTED** if mid-band restores refusal as well as top-of-band does. Then the effect is not specific
to the top of the band, the Qwen3 result was population-specific, and **the specificity leg that C-20
removed from C9/C11/C12 stays removed.** Stated before the arm exists.


### ⛔ R-71 (08:50) — **PR-28 DOES NOT REPLICATE: condition 2 fails on Llama. Mid-band rescue restores refusal there by a margin-clearing amount, so the effect is NOT specific to the top of the band. The specificity leg C-20 removed from C9/C11/C12 STAYS REMOVED, and this branch stops.**

Judge window `p11j_{A,ko,L14,L10}`, job `784963`: 640 rows, **0 nulls**, one pinned
`openai/gpt-4o-mini`, all four arms d10 pool A. New arm `p11_qpos_L10_20260827_081318_733459` —
160/160, `failures: 0`, `frac_rows_scope_live=1.0`, `scope_violations={}`, `fired` 160/160 at 24
positions.

**Precondition passed** (C-20's trap): L10 is a **real** intervention — 14/160 identical to the
knockout arm, against L14's 7/160. The corrected `layer > lo` rule predicted this and was right a
second time.

**Gate passed**: the Llama knockout raises refusal 9 → 35 = **+0.1625**, so there was something to
rescue and R-52's decline rule does not apply.

| condition | requirement | Llama result | |
|---|---|---|---|
| 1 — top of band restores refusal | `|Δ| > 0.0521` **and** `p < 0.05` | **−0.1562** (−25 rows), discordant 27/2, **p = 1.6e-06** | ✅ |
| **2 — mid band does NOT** | `|Δ| ≤ 0.0521` | **−0.0688** (−11 rows), discordant 15/4, **p = 0.019** | **❌ FAILS** |
| 3 — they separate | `> 0.0417` **and** `p < 0.05` | **0.0875**, L10 vs L14 discordant 15/1, **p = 0.00052** | ✅ |

**PR-28 required all three. Condition 2 fails, so the layer-specificity claim is NOT established, and
per the standing rule this branch stops rather than being rescued.**

**What the data actually shows, stated once and not pursued.** On Llama the refusal restoration is
**graded with depth** — mid-band gives back 11 rows and top-of-band 25 — whereas on Qwen3 mid-band gave
back 6 rows *inside* the margin at **p = 0.21**, i.e. nothing detectable:

| | mid band | top of band | separation |
|---|---|---|---|
| Qwen3 (7-17) | −0.0375, p=0.21 | −0.09375 (−15/160), p=0.00073 | 0.0562, p=0.0117 |
| Llama (6-14) | **−0.0688, p=0.019** | −0.1562, p=1.6e-06 | 0.0875, p=0.00052 |

**The two models disagree on exactly the condition that would have made this a claim.** Condition 3 —
the separation — holds decisively in both, and it would be easy to report that alone as a success.
**That is precisely the cherry-pick the pre-registration exists to stop, so it is not being reported
that way.** "Top of band restores more than mid-band" is real in both models; **"the effect is specific
to the top of the band" is false on Llama.**

**⛔ Not pursued further.** The obvious next move is a layer sweep to characterise the Llama gradient.
That is rescuing a failed gate, and PR-13 already forbade scanning layers for this reason. **No
additional layers are run.**

**Consequences, all negative and all recorded:**

* **C9, C11 and C12 do not get their specificity leg back.** C-20 removed it; PR-28 was the attempt to
  restore it properly; the attempt failed. Their **primary effects are unaffected** — they never rested
  on the layer control.
* **R-70's exploratory L12/L17 observation is now known to be model-specific** and is withdrawn as a
  candidate claim. It stays in the log as what it always was: exploratory, never pre-registered.
* **PR-28's declared change of statistic stands and was not the problem.** The paired exact test was
  applied symmetrically, it strengthened C1 (p ≤ 9.5e-07), and here it *sharpened the failure* — L10's
  restoration is significant at p = 0.019, which is what killed condition 2. **A statistic adopted for
  good reasons should sometimes cost you a result, and this one did.**


### 📌 R-72 (09:10) — **The planned experimental programme is COMPLETE. Every pre-registration PR-1…PR-28 has a recorded outcome, every §20 question is answered, declined on evidence, or failed its gate. What remains needs a decision that is not mine.**

Queue empty; no FAILED or CANCELLED job this phase owns; `check_all` 6/6; suite 1085/0 (DR-10).

**§20, closed item by item:**

| question | status |
|---|---|
| Q1 response-query vs prefill | answered (C2, C3) |
| Q2 what changes when the attack dies | answered (C4, C5) |
| Q3 causal rescue | answered (C9, instrument-verified C10) |
| **Q4 low-rank vs distributed** | **DECLINED ON EVIDENCE (R-65)** — its antecedent failed |
| Q5 fourth demonstration pool | answered (R-29) |
| Q6 joint crossed Qwen3 factorization | dropped (R-30), already answered by R-17 |
| **Q7 retrieval/refusal independence on Qwen3** | **ANSWERED (R-70)** — strong half replicates, ASR half declines |
| Q8 GCG/MAC objective | closed with Q4, which gated it |
| *(follow-on)* layer specificity | **FAILED ITS GATE (R-71)** — branch stopped, not rescued |

**Consistency pass on the deliverables, after a day that issued three corrections (C-19, C-20, C-21):**
no withdrawn statement asserts itself unstruck in either deliverable; C7's truncation-robustness is
stated in all three documents; **no document claims layer specificity anywhere.**

**What this phase actually established, in one line each:**

* **C7 is the strongest result**: attack removal is demonstration-specific — confirmed on pool A,
  replicated on pool B, and shown truncation-robust at a 640-token cap where the effect **grew**.
  Three independent populations agreeing in sign at both decisive doses (DR-10's framing).
* **C1 is the most robust**: `demoproc` uniquely restores refusal in three settings, now also at
  paired exact p ≤ 9.5e-07.
* **C11's strong half is model-general** (R-70); its ASR half declines for power on Qwen3.
* **The dissociation stands**: refusal restoration is not the route to attack removal (C2/C12).

**⛔ What remains is ONE item and it is blocked on a decision, not on compute.** R-27's
**benign-register concept bank** — the vehicle for mapping-usage and for lifting lexical generality
above **G = 1**, which is limitation 5 and the phase's largest unaddressed scope limit. It is a
**bank-design change**, the same class as the longer-context bank that had to be authorised before
C7 could be tested. **It is not started, and I am not starting it unasked.**

**Nothing else is justified by current evidence.** The honest alternative to inventing work is to say
the programme is done, and this entry says it.


### 🔒 PR-29 (09:15, written and committed before any arm is submitted) — **lexical generality: C1 on a SECOND CODEWORD. Limitation 5 turns out NOT to need a bank-design change.**

R-72 said the one remaining item was blocked on a decision. **Checking the bank directory instead of
my own summary of it, that was wrong for the cheaper half of the problem.** The repo already contains
codeword-variant banks built by an earlier phase — `basket_bomb`, `button_bomb`, plus `*_club`,
`*_gun`, `*_knife` — and they are **structurally identical** to `d10`:

| bank | rows | blocks | conditions | query kinds | codeword | concept |
|---|---|---|---|---|---|---|
| `d10` | 4560 | 8, same set | 6, same set | 4, same set | `carrot` | `bomb` |
| **`basket_bomb`** | 2736 | **same 8** | **same 6** | **same 4** | **`basket`** | `bomb` |

So **lexical generality G = 1 → 2 for C1 needs no new bank and no design change** — only a `--bank`
swap. The **benign-register concept bank (R-27) is still blocked** and is a genuinely different item;
this does not substitute for it. What this does is remove the cheap half of limitation 5 from behind
that block.

**Gates, run before this was written, each able to stop the branch:**

1. `prompt_families.py --strict` → **336 families checked, 0 violations.**
2. `tokenization_audit.py --strict` on the bank, Llama tokenizer → **rows ok=2736 bad=0 ambiguous=0,
   token-alignment violations = 0.**
3. **The bank must genuinely differ** — PR-12's discipline of checking *sentence-set hashes, not file
   names*: `d10` demo-block set sha **`246ffba411144600`** (1164 distinct) vs `basket_bomb`
   **`206d8e1e5406f08f`** (700 distinct). **Different.**

**Design.** Llama-3.1-8B — as PR-12 chose, because C1's Llama refusal rise (**+0.1625**) is the larger
of the two and therefore the more falsifiable target. Bank `basket_bomb`, `behavioral` ×
`natural_doublespeak` × `core2x2,core2x2_slot3` × `n_examples ∈ {1,2,4,8}` → **`--expect-n 96`**
(6 domains × 4 doses × 4). Five arms: baseline plus the four scopes, at the same band **6-14** and the
same settings as every prior C1 arm — **nothing is retuned for the new codeword.** All five judged in
one window.

#### 📌 The claim under test is C1, fixed before the arms exist, and the conditions are PR-12's

> `demo_processing_only` restores refusal; the other scopes do not.

**REPLICATES if BOTH hold:**

1. `demo_processing_only`'s `kw_refusal` rate exceeds **this bank's own baseline** by more than
   `MARGIN_VS_BASELINE = 0.0521`.
2. `legacy_all_query`, `response_query_only` **and** `query_prefill_only` each stay **within** 0.0521
   of that baseline.

*(PR-12 named only the first two scopes in its condition 2; including the third here is **stricter**,
not looser, and is what C1's sentence — "the other scopes do not" — actually asserts.)*

**The baseline is read from this bank's own baseline arm and is NOT assumed equal to** the d10 Llama
baseline (0.0563). **REFUTED if either condition fails.**

**Reported alongside, per PR-28's declared statistic:** the paired exact test on discordant rows.
**It is reported, not gating** — the margins above remain the pre-registered gate, and this is a
96-row population where the margin is **5.0 rows**.

#### ⛔ Pre-committed as NOT counting, consistent with PR-6, PR-12 and C-11

* **ASR magnitudes and any ranking of arms.** C-11 established these sit inside the margin.
* **The domain sign test's p or floor** — 6 domains here against d10's 10, so the attainable floor
  differs and is not comparable.
* **Refusal dose-response** (C6): single-model and separately refuted on Qwen3 (R-22). Not relitigated.
* **Anything about C7.** The count-matched control needs the `longpre` preamble, which this bank does
  not have; **C7 at G = 2 would need a bank build and is out of scope here.** Lexical generality is
  being lifted for **C1 only**, and the phase's other claims stay at **G = 1**.

**DECLINES if** the baseline refusal on this bank is already so high that a +0.0521 rise has no room —
R-52's underpower rule, checked before the conditions are read.


### 🏆 R-73 (10:05) — **PR-29 REPLICATES: C1 holds on a SECOND CODEWORD. Lexical generality for C1 goes from G = 1 to G = 2. ⚠ And I repeated a process miss: PR-29 had no truncation gate, and on this bank the check is untestable.**

Judge window `g2j_{A,legacy,qpre,demoproc,respq}`, job `785034`: 480 rows, **0 nulls**, one pinned
`openai/gpt-4o-mini`. All five arms 96/96 with `DONE.json`, `frac_rows_scope_live = 1.0` and
`scope_violations = {}` on every scope, `n_failed = 0`, one run dir per tag.

**Decline gate passed**: this bank's own baseline refusal is **2/96 = 0.0208**, so there was room for a
+0.0521 rise. The baseline was read from this bank's own arm, not assumed from d10.

| scope | refusal | rate | Δ vs baseline | within ±0.0521? | paired exact |
|---|---|---|---|---|---|
| baseline | 2 | 0.0208 | — | — | — |
| `legacy_all_query` | 0 | 0.0000 | −0.0208 | ✅ within | 2/0, p=0.50 |
| `query_prefill_only` | 0 | 0.0000 | −0.0208 | ✅ within | 2/0, p=0.50 |
| **`demo_processing_only`** | **14** | **0.1458** | **+0.1250** | **clears** | **1/13, p=0.0018** |
| `response_query_only` | 0 | 0.0000 | −0.0208 | ✅ within | 2/0, p=0.50 |

**Both pre-registered conditions hold.** `demo_processing_only` clears the margin by **+0.1250 (12
rows against a 5.0-row margin, 2.4×)**; all three other scopes stay inside it — in fact all three go to
**exactly zero refusals**.

**C1 now holds in FOUR independent settings**, and the codeword is a genuinely new axis:

| setting | model | pool | codeword | rise |
|---|---|---|---|---|
| 1 | Llama | A | `carrot` | +0.1625 |
| 2 | Qwen3 | A | `carrot` | +0.1312 |
| 3 | Llama | B | `carrot` | +0.1938 |
| **4** | **Llama** | **basket_bomb** | **`basket`** | **+0.1250** |

**Limitation 5 (lexical G = 1) is lifted for C1, and for C1 only.** Every other claim in this phase —
C7 included — remains at **G = 1**, exactly as PR-29 pre-committed.

#### ⚠ The process miss, stated plainly

**PR-29 contained no truncation gate, and it should have.** C-19 established the rule hours ago and
PR-26 put it into a gate for C7 — then I wrote PR-29 without carrying it across. **That is precisely
the failure C-19 diagnosed** ("a rule that lives in a prior review rather than in the pre-registration
is a rule that gets skipped"), repeated one pre-registration later.

I ran the check anyway, **with** the result rather than after it, and it is untestable on this bank:

| | truncation | both-terminated subgroup |
|---|---|---|
| baseline | **0.938** | |
| `demo_processing_only` | **0.854** | **1 row — CANNOT TEST** |
| `legacy_all_query` | 0.990 | |
| `response_query_only` | 0.979 | |

This bank truncates far harder than `d10` on the *same model* (**0.938 vs 0.581** at baseline), and
median new tokens is **192 — the cap — for every arm.** So R-73's numbers are ASR-era caveated in the
same way C-19 forced onto C7: **an ASR/refusal read over the first 192 tokens, with truncation
robustness UNMEASURED on this bank.**

**What that does and does not threaten.** Refusal is `kw_refusal`, a **deterministic** detector that
flipped **0/160** on identical text (DR-10), and refusal markers occur at the *start* of a completion,
so truncation at 192 tokens is unlikely to hide one. That is an argument, not a measurement. **PR-30
below makes it a measurement**, using PR-26's design, which already worked once.

---

### 🔒 PR-30 (10:10, pre-registered before the arms are submitted) — **the truncation test PR-29 should have contained.**

Identical to PR-26's design, which resolved the same question for C7. Bank `basket_bomb`, Llama,
band 6-14, **two arms only** — baseline and `demo_processing_only`, because C1's condition 1 is the
claim at risk and the other three scopes sit at exactly zero refusals. **`--max-new 192 → 640`, all
four doses, nothing else changed.**

**Gates, in order, branch stops if one fails:**

1. `frac_stop_length < 0.15` on **both** arms. If this bank still truncates at 640, the cap is not the
   binding constraint here and the test cannot be run — **say so and stop, do not raise the cap again.**
2. `|frac_stop_length(baseline) − frac_stop_length(demoproc)| < 0.10`.
3. Baseline refusal **≤ 0.10**, so a +0.0521 rise still has room on the new population.

**Then PR-29's condition 1, unchanged**: `demo_processing_only` exceeds the baseline by **> 0.0521**.

* **CONFIRMS** → R-73's truncation caveat is discharged, as PR-26 discharged C-19's.
* **REFUTED** → C1's fourth setting is an artifact of the 192-token cap, R-73 is a correct reading of
  a confounded measurement, and **lexical generality reverts to G = 1.** Stated before the arms exist.


### 🔎 R-74 (10:40) — **Reference audit: every artifact path and every job id cited in the deliverables RESOLVES. PR-30 is queue-blocked, and the standing stall rule cannot be applied here — recorded rather than worked around.**

**PR-30 status.** `785044` / `785045` have been PENDING for **~30 minutes** on `(Resources)` and
`(Priority)`. All four requested nodes are in `mix` state; the cluster is simply busy.

**⛔ The stall rule does not apply and is deliberately not adapted.** The standing rule is *"if a job is
PENDING over 30 minutes, scancel and resubmit with a different config"*. **`scancel` is forbidden
here.** Submitting replacements *without* cancelling would leave two jobs racing to write the same
tag — **C-17's double-run, which this phase has already paid for once.** So the arms are left alone and
the PR-30 read waits. **Nothing else is blocked by it.**

**Reference audit — the "execute the manifest" discipline that caught C-13**, run because it needs no
GPU and the queue was idle time:

| document | citation form | cited | unresolvable |
|---|---|---|---|
| `RESEARCH_HANDOFF.md` | artifact paths | 9 | **0** |
| the sprint summary | **job ids** | 74 | **0** |
| this log | artifact paths | 28 | **0** |

* **37 artifact paths**, each resolved on disk (prefix citations such as `p4bj_` resolved by prefix,
  which is what they assert).
* **74 job ids** in the summary's run table, **every one** with a log under
  `outputs/boombness/logs/`. The summary cites runs by job id rather than path; that is a legitimate
  reference form **only if the ids are traceable**, so they were checked rather than assumed.
* **First-pass false positives are worth recording**: the naive check reported 11 "missing" paths,
  all of which were prose **prefixes** (`p4b`, `p4bj_`, `boomb_`). A checker that flags those as
  broken would train me to ignore it. The refined check resolves prefixes; **0 genuinely unresolvable
  references remain.**

**Housekeeping.** Removed a **0-byte file whose *name* was a fragment of my C-20 commit message** —
created 05:46 when unescaped quotes in `git commit -m` turned part of the message into a shell
redirect. Verified empty before deleting. The remaining working-tree modifications
(`BOOMBNESS_DSURFACE_...`, two other sprint summaries, and a regeneration of
`boombness_prompt_bank_meta.json`) are **the concurrent writer's and were not touched or staged.**


### 🏆 R-75 (11:25) — **PR-30 CONFIRMS, and more sharply than it had to: with truncation eliminated, the refusal effect is IDENTICAL ROW-FOR-ROW. R-73's caveat is discharged and lexical generality G = 2 stands.**

Arms `g3A640_20260827_105828_...` and `g3dp640_20260827_105828_1094827`, judged in one window
(`g3j_{A,dp}`, job `785197`): 192 rows, **0 nulls**, one pinned `openai/gpt-4o-mini`.
`frac_rows_scope_live = 1.0`, `scope_violations = {}`, `n_failed = 0`.

**All three gates pass:**

| gate | requirement | result |
|---|---|---|
| 1 — cap released | `frac_stop_length < 0.15` on both | **0.000 / 0.000** (was **0.938 / 0.854**) ✅ |
| 2 — truncation no longer separates | `< 0.10` | **0.000** ✅ |
| 3 — power on the new population | baseline refusal ≤ 0.10 | **2/96 = 0.0208** ✅ |

Longest completion **500 tokens against a 640 cap**; median new tokens 308 (baseline) and 354
(`demoproc`). The cap is genuinely released, not raised until the number looked acceptable.

**PR-29's condition 1, unchanged, on the untruncated population:**

> refusal **2 → 14**, **Δ = +0.1250**, discordant **1/13**, exact **p = 0.0018**

**That is the same to the row as the 192-token result.** So I checked whether the 640 run had somehow
reused the old generations — the C-17/C-20 class of failure:

| check | result |
|---|---|
| generations identical between the 192-cap and 640-cap `demoproc` arms | **15/96** — the 15 that already terminated under 192. **No reuse.** |
| rows refusing at 192 vs at 640 | **14 and 14, and they are the SAME 14 rows** — 0 only-at-192, 0 only-at-640 |
| baseline refusing rows | **2 and 2, the same 2 rows** |

**81 of 96 completions changed and not one refusal decision moved.** That is a much stronger statement
than "the effect survives": **refusal is invariant to the generation cap at the row level.**

**Why, and what it generalises to.** R-73 argued that refusal markers occur at the *start* of a
completion, so a cap at 192 tokens cannot hide one. **That was an argument; this is the measurement**,
and it says something beyond this bank: **DR-2's truncation caveat is an ASR caveat, not a refusal
caveat.** C1 is a refusal claim in all four of its settings, so **C1's truncation exposure is
essentially nil** — which is the opposite of C7, whose ASR reading genuinely needed PR-26 to rescue it.

**Consequences:**

* **R-73's scope sentence is discharged.** C1's fourth setting is not an artifact of the 192-token cap.
* **Lexical generality G = 2 stands for C1.** Limitation 5 is lifted for C1 and, as PR-29
  pre-committed, **for C1 only** — C7 and every other claim remain at **G = 1**.
* **PR-29's process miss (no truncation gate) cost nothing in the end** — but it was still a miss, and
  R-73 records it. The fix was to run the test, not to argue the caveat away.


### 📌 R-76 (11:40) — **Final status: no further experiment is justified without a decision. I considered a third codeword and a concept variation, and am declining BOTH — one is low-information, the other would be inventing a limitation to solve.**

Queue empty; no FAILED or CANCELLED job; `check_all` 6/6.

**Considered and declined: a THIRD codeword** (`button_bomb`, structurally identical, ~40 min of GPU).
C1 now holds at **+0.1625, +0.1312, +0.1938, +0.1250** across two models, two pools and two codewords,
every one clearing its margin by **2.4-3.7×**. A fifth setting is very likely to confirm and would add
almost nothing: **DR-10's framing is that what carries a claim is independent populations agreeing, and
four already do.** Declined for low information, not for cost.

**Considered and declined: a CONCEPT variation** (`basket_gun` / `basket_club` / `basket_knife` exist,
holding the codeword fixed while varying the harmful concept). It is a genuinely different generality
axis and I was ready to pre-register it — **then I checked the recorded limitations and concept
generality is not among them.** Limitations 1-8 name demonstration-specificity, mapping usage, the
192-token ASR window, `kw_refusal`'s lexicality, **lexical** generality, coherent non-compliance,
the "% of rise" rule, and layer specificity. **Nothing claims concept generality.** Running it would be
**inventing a limitation in order to solve it**, which is the failure mode this log exists to prevent.
Declined.

**Corrected a stale limitation instead.** Limitation 5 read *"Lexical generality G = 1 (one codeword)
throughout this phase"* — **false as of R-73/R-75.** It now reads **G = 2 for C1, G = 1 for everything
else**, with the reason C7 cannot follow: its count-matched control needs the `longpre` preamble that
the codeword banks do not have, so C7 at G = 2 requires a bank build. No guard caught this because it
is not a retraction — **a claim strengthening can leave a deliverable stale exactly as a retraction
can.**

#### ⛔ What is left, precisely

**One item, and it is the one that was blocked from the start**: **limitation 2 — mapping usage is
unreadable, and it needs a benign-register concept vocabulary** (R-27). That is a **bank-design
change**, the same class as the longer-context bank which had to be authorised before C7 could be
tested. It is **not started and will not be started unasked.**

Everything else is closed: **PR-1…PR-30 all have recorded outcomes**, §20 is fully resolved (R-72), the
deliverables' 37 artifact paths and 74 job ids all resolve (R-74), and the day's four corrections
(C-19, C-20, C-21, and PR-28's failed gate) are propagated everywhere they touch.

**The honest statement is that the phase is finished pending one decision, and this entry makes it
rather than manufacturing a fifth codeword to look busy.**


### 📌 R-77 (11:50) — **Limitation 2 authorised. Scoping it first: the benign-register mapping ALREADY EXISTS in the bank as the `benign_remap` condition, and the concept-usage flag is already parameterised. This may need no bank build at all — the same surprise as limitation 5.**

The user authorised R-27's bank-design change. **Before building anything I read the code**, and the
instrument R-27 prescribed is largely already present.

**R-27's requirement, verbatim:** *"the flag would have to be a concept term that is **not** itself
harmful content — the mapping expressed in a benign register."*

**What already exists:**

* **`benign_remap` (cell F)** in `CONDITIONS`, described in the source as *"benign-valence sentences
  from a DIFFERENT domain remapped onto the codeword, so the structure and the remapping are present
  but the taught meaning is harmless."* Concretely (`prompt_families.py:319-323`) it draws from the
  `<domain>|remap` pool — sentences about **`bicycle`** in an *equipment-inventory* register — and
  substitutes `bicycle → carrot`. **So the demos teach `carrot` behaves like a bicycle, in a benign
  register, with no harmful vocabulary anywhere.**
* **The flag is already parameterised**: `completion_phenotype.lexical_phenotype(text, stop_reason,
  codeword, concept_terms)` takes `concept_terms` as an argument. Pointing it at bicycle vocabulary
  instead of bomb vocabulary is a call-site change, not a code change.
* **A built-in floor**: `benign_remap` exists at `n_examples ∈ {0, 4, 8}`. **The `n = 0` rows teach no
  mapping at all**, so they are a natural negative control for concept usage rather than an assumed one.

**Why this dissolves R-27's confound.** R-27 was uninformative because *"mentions bomb/explosive/
detonate"* and *"is a successful jailbreak"* were nearly the same event, so concept usage was
confounded with the outcome. **`bicycle` is not harmful content and does not move StrongREJECT**, so
"did the model use the mapping" becomes measurable independently of "did it comply."

**Population, counted not assumed:** `benign_remap` has **120 rows** in `d10` — 60 `behavioral` and 60
`semantic_one_word`, at `n_examples ∈ {0, 4, 8}`, all in the `extra_conditions` block. So the
behavioural population is **60 rows, 20 per dose.** That is **small** — the margin at n = 20 is
**1.0 row** — and it is the honest constraint on this branch, replacing "we need a new bank" with
"we have an instrument but a thin population."

**⛔ Nothing is run and nothing is pre-registered yet, deliberately.** The one real design decision is
**which terms count as bicycle vocabulary**, and that list must be fixed **before** any completion is
read — and derived from the **remap pool's own sentences**, never from the completions, or it becomes
a list tuned to produce an effect. That is the next tick's work, as PR-31.

**If the population proves too thin**, the fallback is the bank build the user authorised — generating
`demo_pools` with a benign concept via `run_demo_pools.sh` (`DP_CONCEPT`/`DP_CODEWORD` are already
parameters). **The authorisation is not being spent until it is needed**, which is the same judgement
that turned limitation 5 into a `--bank` swap rather than a build.


### 🔎 DR-11 (20:05, 4h DEEP REVIEW) — **Suite 1085/0. Every number published since DR-10 recomputes EXACTLY from artifacts. One rendering nit fixed. And R-75 licenses retiring a whole class of caveat: refusal metrics are truncation-invariant by measurement.**

**Suite** `1085 passed, 7 skipped` (434s). Queue empty; no FAILED/CANCELLED job this phase owns.

**Independent recompute of everything published since DR-10** — read from `results.jsonl`, not from
the log:

| result | published | recomputed |
|---|---|---|
| R-70 `L17` refusal Δ | −0.0937 | **−15/160 = −0.09375** ✅ |
| R-70 discordant / p | 17/2, p=0.00073 | **17/2, p=0.00072861** ✅ |
| R-71 `L14` Δ | −0.1562 | **−0.1562** ✅ |
| R-71 `L10` Δ, discordant, p | −0.0688, 15/4, p=0.019211 | **−0.0688, 15/4, p=0.019211** ✅ |
| R-73 (192 cap) | +0.1250, 1/13, p=0.0018 | **2→14, +0.1250, 1/13, p=0.0018311** ✅ |
| R-75 (640 cap) | +0.1250, 1/13, p=0.0018 | **2→14, +0.1250, 1/13, p=0.0018311** ✅ |

**One rendering nit, fixed rather than argued.** R-70's Δ is **exactly 15/160 = 0.09375** — a true
half-way case. I rendered it `−0.0937` (truncation); round-half-up gives `−0.0938`. **Neither changes
any decision** (the margin is 0.0521 and the effect clears it either way), and this is *not* a C-14
situation — there is no round-then-divide artifact, just an exactly-representable half. **The fix is to
stop rendering it at 4 dp at all**: all 7 occurrences now read **`−0.09375 (−15/160)`**, which is
DR-5's rule — rows travel with the rate.

**Liveness, provenance, overwrites — 13 post-DR-10 arms swept.** Every intervention arm
`frac_rows_scope_live = 1.0`, `scope_violations = {}`; every arm `DONE` at its expected row count;
`n_failed = 0`; **exactly one run directory per tag**; banks correct per family (`d10` for the Q7/PR-28
work, `basket_bomb` for PR-29/30).

#### 🏆 The review's real finding: R-75 retires the truncation caveat for an entire metric class

R-75 measured that between a 192- and a 640-token cap, **81 of 96 completions changed and not one
refusal decision moved** (14 refusals, the *same 14 rows*; baseline 2, the *same 2 rows*). Combined
with DR-10's measurement that `kw_refusal` disagrees on **0/160** rows of byte-identical text:

> **A refusal count has no measurable noise from the judge and none from the generation cap. Its only
> uncertainty is population sampling.**

That matters across the phase, because **every claim in this branch is a refusal claim**: C1 in all
four settings, R-70's condition 1, R-71's conditions. **Their truncation exposure is nil, and it no
longer needs a per-claim check** — which is why `p11_qpos_L10`'s 0.562 truncation, flagged by this
sweep, does **not** require a PR-26-style rerun.

**⚠ Scope of that generalisation, stated rather than glossed:** the cap-invariance was measured on
**one bank and one model** (`basket_bomb`, Llama). It is **strong evidence, not proof**, that refusal
detection is cap-insensitive in general. The mechanism is transparent — refusal markers occur at the
*start* of a completion — but the honest label is *measured once, argued generally*.

**By contrast, ASR keeps its caveats**: 9/160 judge flips on identical text (DR-10) **and** a genuine
cap sensitivity that C7 needed PR-26 to clear. **The phase's ASR claims and its refusal claims do not
sit on the same evidential footing, and the write-ups should say so.**

**No correction issued this round** beyond the rendering fix. Recorded explicitly.


### 🔒 PR-31 (20:15, written and committed before any arm is submitted) — **limitation 2: does the intervention stop the MAPPING BEING USED, measured in a benign register where usage is not a restatement of harm?**

R-27 killed PR-11 because *"mentions bomb/explosive/detonate"* and *"is a successful jailbreak"* were
nearly the same event. **The `benign_remap` condition removes that identity**: its demos teach
`carrot` behaves like a **bicycle** (the `<domain>|remap` pools, equipment-inventory register,
`bicycle → carrot` substituted), and **bicycle is not harmful content and does not move StrongREJECT.**

#### 📌 The flag, fixed here, derived from POOL TEXT and never from completions

**Primary: the completion contains `bicycle`** (case-insensitive) — `REMAP_SOURCE_WORD`, defined in
`demo_pools.py`, not chosen by me.

**The property that makes it clean, measured:** `bicycle` appears in **0 of 60** `benign_remap`
behavioural prompts — 0 demo blocks and 0 full prompts, because the pool substitutes it to the
codeword. **A completion that says `bicycle` INFERRED the mapping; it cannot have copied it.**

**Secondary (reported, never gating): a 16-term list built by a mechanical rule**, stated before the
terms were looked at — *appears ≥5 times in the `remap` pools AND zero times in the `harm`, `benign`
and `filler` pools*, which strips shared domain vocabulary:

`bicycle, repair, tires, frame, riders, racing, lane, races, rode, ride, handlebars, short, parking,
rides, cyclists, riding`

**⚠ I am not hand-editing that list**, even though `repair`, `short`, `lane` and `parking` are generic
enough to fire on unrelated text. Removing them by eye is exactly the tuning this design forbids.
**Instead the generic-contamination problem is solved by making the primary flag a single unambiguous
term**, with the list kept only as a sensitivity check.

#### Design

`d10` bank, `condition = benign_remap`, `query_kind = behavioral`, `n_examples ∈ {0, 4, 8}` →
**`--expect-n 60`, 20 per dose, 10 domains.** Llama-3.1-8B, band **6-14**, two arms: baseline and
`demo_processing_only`. Nothing retuned. **`n = 0` teaches no mapping and is the NATURAL FLOOR** — a
measured floor, not an assumed one.

**Primary population is `n ∈ {4,8}` POOLED (40 rows, margin 2.08 rows).** Per-dose is reported but 20
rows carries a 1.04-row margin and is not read as decisive on its own — DR-10's rule.

**Statistic.** The flag is a deterministic substring test, the same class as `kw_refusal`, which DR-11
showed has no judge and no cap noise. So the **paired exact test is appropriate here** and PR-28's
declaration extends to it — but as there, **PR-3's margin remains a required gate and the exact test is
required alongside it, never instead.**

#### 📌 Conditions

**GATE first — is the mapping used at all?** Baseline `bicycle` rate at `n ∈ {4,8}` must exceed the
`n = 0` floor by **> 0.0521**. **If the model does not name the concept even at baseline, there is
nothing to knock out and this DECLINES for power** (R-52's rule), and limitation 2 is recorded as
*needing the authorised bank build after all* rather than as a null.

**Only if the gate passes:**

1. `demo_processing_only` reduces `bicycle` usage vs baseline by **> 0.0521** on the pooled population,
   **and** paired exact **p < 0.05**.
2. The **direction** is a reduction, not an increase.

* **CONFIRMS** → the intervention stops the mapping being *used*, not merely stops harm — the first
  clean statement on limitation 2, and a genuine complement to R-16/R-17's finding that the mapping
  *survives* in a forced-choice probe. **Those two together would be the interesting result: retrievable
  but not used.**
* **REFUTED** → usage is unchanged while the phase's other work shows behaviour collapsing, which would
  say the intervention removes the behaviour without removing mapping use.
* **DECLINES** → gate fails; spend the authorised bank build.

**⛔ Pre-committed as NOT counting:** ASR and StrongREJECT on this population (there is no harm to
measure — that is the entire point), the 5-way phenotype cascade (PR-11 forbade it and DR-2's
truncation reason still holds), and any per-dose cell read alone.


### ⛔ C-22 (20:40) — **PR-31's intervention arm was INCOHERENTLY SPECIFIED and the pre-flight refused it: I asked a demonstration-knockout to run on 20 rows that have no demonstrations. Caught by the instrument, before any outcome existed.**

`br_dp` (job `786870`) **FAILED in 7 minutes**, before generating a single row:

> `REFUSING before generating: 20 of 60 rows cannot carry this knockout (20 without a demo block…).
> Per n_examples: {'0': {'n': 20, 'ok': 0, 'bad': 20}, '4': {…'ok': 20…}, '8': {…'ok': 20…}}.
> Fix the arm or the population — do NOT rescope to the feasible rows…`

**The guard is right and the error is mine.** PR-31 specified *"two arms: baseline and
`demo_processing_only`"* at `--expect-n 60`, but `n_examples = 0` rows have **no demonstration block**,
so `demo_processing_only` is not merely infeasible there — **it is undefined.** You cannot knock out
demonstrations that do not exist.

**Why this is a specification fix and NOT a rescue of a failed gate.** The standing rule is that a
failed gate stops a branch. This was not a scientific gate: nothing was measured, no outcome was read,
and **PR-31's analysis section already specified the correct populations** —

> *"`n = 0` teaches no mapping and is the NATURAL FLOOR"* … *"Primary population is `n ∈ {4,8}`
> POOLED (40 rows)"*

The **floor comes from the baseline arm**, which correctly ran all 60 rows (verified: 60/60,
`n_failed = 0`, 20 per dose). The **intervention arm never needed `n = 0` at all.** So the argsfile
contradicted the pre-registration it was supposed to implement, and the fix **restores** PR-31 rather
than amending it. `br_dp` is resubmitted at `--n-examples 4,8 --expect-n 40`. **No condition, margin,
population or flag changes.**

**⚠ What made this safe to fix rather than fatal:** the failure happened **before generation**, so
there is no outcome to have been influenced by the correction. Had the arm silently rescoped itself to
the 40 feasible rows — which is exactly what the guard's message forbids — **I would have compared a
40-row intervention against a 60-row baseline and never noticed**, and the floor rows would have been
folded into an effect estimate. That guard was written for a different sprint's mistake and it just
paid for itself again.

**The lesson, which is the same one C-19 and PR-29 taught in a different costume:** I wrote the correct
design in the analysis section and then wrote an argsfile that did not match it. **A pre-registration
and the command that implements it are two artifacts, and only one of them runs.**


### ⛔ R-78 (21:10) — **PR-31 DECLINES: the gate fails on its pre-registered flag. And the diagnostic shows exactly why — my flag was too narrow — which I am recording as an instrument lesson and explicitly NOT using to re-gate this data.**

Artifacts: `br_A_20260827_...` (60/60, `n_failed = 0`) and `br_dp_20260827_204727_2209758`
(40/40, `frac_rows_scope_live = 1.0`, `scope_violations = {}`). *(A second `br_dp` directory exists
from the run C-22 refused — no `gens.jsonl`, no `DONE.json`, an orphan carrying no data.)*

**The gate, as pre-registered — baseline `bicycle` rate must exceed the `n = 0` floor by > 0.0521:**

| dose | n | rows containing `bicycle` | rate |
|---|---|---|---|
| **0 (floor)** | 20 | **0** | 0.0000 |
| 4 | 20 | 1 | 0.0500 |
| 8 | 20 | **0** | 0.0000 |

**Floor 0.0000, baseline at n ∈ {4,8} = 0.0250, lift +0.0250 — inside the 0.0521 margin. GATE FAILS.**
Per PR-31 this is a **DECLINE for lack of power**, not a null: the model essentially never *names* the
inferred concept in free generation, so there is nothing for the knockout to remove.

#### 🔎 The diagnostic, recorded as an instrument lesson and NOT as a result

The pre-committed secondary list tells a different story. Splitting it into terms that are
bicycle-**specific** versus generic:

| | n = 0 floor | n ∈ {4,8} baseline |
|---|---|---|
| rows hitting **any bicycle-specific term** (`tires`, `racing`, `handlebars`, `ride`, `cyclists`, `races`, `bicycle`) | **0/20** | **11/40** |
| generic terms (`repair` 8, `frame` 4, `lane` 3) | 0/20 | fire too |

**So the mapping evidently IS being used** — the model writes about tires, racing and handlebars — **it
just rarely says the word `bicycle`.** My primary flag asked whether the model *names* the concept when
the thing to ask was whether it *deploys the concept's vocabulary*.

**⛔ I am not switching to the specific-subset flag on this data, and that restraint is the point.**
Doing so would be three forbidden moves at once: adopting a statistic **after** seeing that it works,
**hand-splitting** the 16 terms into "specific" and "generic" by eye — which PR-31 explicitly forbade —
and **re-gating a failed gate on the same completions.** The 11/40-vs-0/20 split is suggestive and it
is **not a claim**; it is a specification for the next instrument.

**What carries forward.** The flag must be *concept-vocabulary* based and derived mechanically, and the
concept must be one the model will actually name. That is a **bank-design** requirement — precisely the
build the user authorised — and it is now **motivated by measurement rather than by argument**, which is
worth more than the failed test cost.

**PR-31's own decline clause is therefore executed as written:** *"DECLINES → gate fails; spend the
authorised bank build."*


### ⛔ C-23 (21:20) — **CORRECTION to R-64: I framed a 1-2 row change as the effect "GROWING" when the cap moves nothing detectably. Found by cross-checking a CONCURRENT WRITER's independent analysis of my own artifacts.**

Another session pushed **V-1/V-2/V-3** onto this branch while PR-31 was running (`4da920c1`,
`8aa67ee6`, `03c06b75`). My commits are all intact as ancestors and nothing of theirs was touched.
**V-3 analyses the same `g2A`/`g3A640` and `q16j`/`p26j` artifacts I produced**, as a within-row cap
natural experiment — so I verified their numbers against the artifacts myself rather than accepting
the table.

**Recomputed independently, on the 80 rows PR-26 ran:**

| | cap 192 | cap 640 |
|---|---|---|
| baseline | 10/80 | 11/80 |
| `demoproc` | **1/80** | **1/80** |
| delta | −0.1125 | −0.1250 |

**Within-row effect of the cap on each arm** (the right test, since greedy decoding makes the 640 run
a continuation of the 192 run):

| arm | down | up | exact p |
|---|---|---|---|
| baseline | 3 | 4 | **1.0** |
| `demoproc` | 1 | 1 | **1.0** |

**The cap moves neither arm detectably.**

**⚠ And one of those two nulls is UNINFORMATIVE, which the concurrent session flagged and I am
adopting.** `demoproc` has **1 discordant pair**; at n=1 discordant, **no split reaches α = 0.05 in
either direction**, so its `p = 1.0` **could not have come out any other way** and is *not* evidence of
absence. The baseline's 7 discordant pairs are informative; `demoproc`'s single pair is not. This is
the same rule as PR-1's attainable-floor `2/2^k` — *a p at its floor is a design fact, not a result* —
and I failed to apply it to my own null.

**What I wrote in R-64:** *"the effect **grows** at n=8 (−0.1250 → −0.1750) … `demoproc` now removes
7 of 7 attacks"* and, as the headline, *"removes MORE attack, not less."* **That is a per-dose slice of
a 1-2 row change.** Pooled it is −0.1125 → −0.1250 — one row — and the within-row test says p = 1.0.
**"Grows" is not supported and is withdrawn** from the claim table, the handoff and the sprint summary.

**What still stands, unchanged:** PR-26's three gates passed, and PR-23's conditions hold at both caps.
The truncation-artifact hypothesis predicted the effect would **shrink** when completions finished; it
did not shrink. **"Not an artifact of the cap" survives; "grows" does not.** R-64's verdict of CONFIRMS
is correct; its *direction* language was not.

**And a premise of mine was wrong, which is the more useful part.** C-19 reasoned that truncated
completions would score *lower*, so truncation would depress ASR. V-3's Llama pair shows **12 rows
flipped 0→1 and 5 flipped 1→0** when allowed to finish — **truncation is not a one-way suppressor**; a
completion cut at 192 tokens sometimes scores *higher*, because it was cut before the model hedged or
wandered. **Any argument of the form "the old number was depressed by truncation" is wrong on its
face**, including the one I used to motivate PR-26.

**Why this is worth recording beyond the fix.** I ran PR-26, passed every gate, and still reached for a
directional story the data did not carry — and the thing that caught it was **someone else analysing my
artifacts a different way.** DR-11 had already given me the tool to catch this (*"no single cell is
decisive alone"*) and I did not apply it to my own headline.


### 📌 R-79 (21:15) — **Spending the authorised bank build, with the design fixed by R-78's diagnostic rather than by my original guess. Also: three PENDING jobs on this account are NOT mine and are left alone.**

**Queue hygiene first.** `787094`/`787095`/`787096` are PENDING, submitted **21:09:07**, with **no
`BOOMB_ARGSFILE` I wrote** and no corresponding file in `runargs/p17/` (my newest is `br_dp.txt` at
20:41). They arrived as the concurrent session pushed V-3 at 21:07. **They are not mine and are not
touched**, on the same rule as `779083`/`779084`. Recorded so a later tick does not mistake them for
this phase's work — C-17's lesson was that job ownership must be established from evidence, not from
timing.

**Is the build still justified after C-23?** Yes, and the reasoning is checked rather than assumed:
limitation 2 remains open and *recorded*; PR-31's decline clause names the build explicitly; the user
authorised it; and R-78's diagnostic showed the phenomenon **is** present and measurable
(**11/40 vs 0/20** on concept-specific vocabulary) — the instrument was wrong, not the question. The
concurrent V-track is redefining the **ASR** protocol, which does not intersect this branch's
refusal/usage metrics.

#### What R-78 changed about the design

My original guess was that limitation 2 needed a **benign concept**. That was half right. R-78 showed
the actual failure was narrower: **the model deploys the concept's vocabulary but does not name the
head noun**, so a single-word flag misses it while the population (40 rows) is too small to carry a
vocabulary flag with a floor.

So the build targets **three** things, not one:

1. **A benign concept** — so usage is not a restatement of harm (R-27's original requirement).
2. **A concept the model will NAME as well as describe** — `forklift`, chosen because its vocabulary
   is distinctive (*tines, mast, pallet, load, operator*) **and** it sits naturally in the incident-log
   / safety-inspection register the `harm`-valence pool prompts already use, so no prompt template is
   rewritten for it.
3. **The full core-2×2 behavioural population** — `natural_doublespeak` at `n_examples ∈ {1,2,4,8}`,
   i.e. **160 rows with a dose ladder**, instead of `benign_remap`'s 40 rows at two doses.

**⛔ `forklift` deliberately avoids `bicycle`**, which is `REMAP_SOURCE_WORD` (`demo_pools.py:194`).
Reusing it would collide with the `benign_remap` control inside the same bank and make "used the
mapping" ambiguous between two different taught mappings.

**Launched: job `787099`**, `run_demo_pools.sh` with `DP_CONCEPT=forklift DP_CODEWORD=carrot
DP_SEED=20260827` → `demo_pools_benign_forklift.json`. CPU-killable, not the login node (the standing
rule about `import openai` hanging under NFS contention).

**⛔ Nothing is pre-registered yet, and the ordering matters:** the pool must exist first, because
**PR-32's flag will be derived mechanically from the NEW pool's sentences** — the same rule that
produced PR-31's list, which is sound even though PR-31's *choice of primary* was not. Deriving it from
the old bank, or from any completion, would be the tuning this log exists to prevent.

**Gates that will stop this branch before any arm runs:** pool generation succeeds and is
content-distinct → `prompt_families.py --strict` 0 violations → `tokenization_audit --strict`
0 alignment violations → the bank regenerates the canonical banks byte-identically (C-10's test).


### ⛔ C-24 (21:25) — **SCOPE CORRECTION to C5, surfaced by the concurrent session's audit: the within-family bridge covers `core2x2` families ONLY, because the forced-choice probe was never generated for any other block. I reported "48 families" without saying it is half, or which half.**

The peer's claim ledger flags my binding-survival claim as `NEEDS_RERUN`, citing
*"family_missing_one_side — 144/288 pairs dropped is a bank/join defect."* **The count is right, the
diagnosis is not**, and both matter.

**Verified on my own artifacts** — every bridge run, three arms each:

| run | `n_failed` | reason | families kept per arm |
|---|---|---|---|
| `bridge_20260825_101613_3117657` | 144 | `family_missing_one_side` ×144 | **48** |
| `qbridge_20260825_104155_3190213` | 144 | same | **48** |
| `REPRO_R16_20260826_051035_1020533` | 144 | same | **48** |

**Why the families are missing — checked against the bank rather than inferred:**

| block | behavioural rows | forced-choice probe rows |
|---|---|---|
| `core2x2` | 72 | **72** |
| `core2x2_slot3` | 48 | **0** |
| `strength` | 48 | **0** |
| `consistency` | 36 | **0** |
| `position` | 12 | **0** |
| `role_style` | 180 | **0** |
| `families` | 72 | **0** |

**468 behavioural family stems, 72 probe stems, 72 in both, 396 behavioural-only.** The probe was
**only ever generated for `core2x2`.** So the dropped families cannot be recovered by fixing a join —
**the other side does not exist.** It is a bank-design fact, and `family_missing_one_side` is the
ledger doing its job, not a silent subset (contrast C-13, where rows *were* silently dropped).

**What is actually wrong is my reporting.** `RESEARCH_HANDOFF.md` records C5 as *"48 families/model"* —
true, but it does not say that this is **half the eligible behavioural families**, nor that the missing
half is **systematically the other blocks**, including the `core2x2_slot3` position variant. **A reader
would take 48 as the population rather than as a `core2x2`-only subset.** That is now stated.

**Does it threaten C5?** No, and I am not claiming a correction I did not earn: the bridge is a
**within-family** 2×2, so restricting to `core2x2` costs power and generality, not validity. But C5's
scope is narrower than written — **it is a statement about `core2x2` families**, and the peer's
suggestion that recovering slot3 "would roughly double k" is right about the payoff and wrong about the
cost: it needs **new probe generation**, not a code fix.

**Credit where it is due.** I recomputed C5's numbers in DR-10 and DR-11 and never asked *"48 out of
how many?"* — the audit did, and that is the question that found this.


### ⚠ R-80 (21:35) — **The forklift pool generated cleanly, but applying PR-31's UNCHANGED rule to it exposes two problems, and I am reporting them instead of relaxing the rule to get a usable flag.**

Pool `demo_pools_benign_forklift.json` (job `787099`) is sound as a generation:
`codeword=carrot concept=forklift`, seed `20260827`, 40 pools × 40 sentences, 10 domains,
`content_sha16 = 567eb1775678406d`, sentence-set sha **`a73553f7801fe8e1`** vs d10's
**`8539cbfc3be8b714`** — genuinely distinct.

**Applying PR-31's rule verbatim** — *concept-pool count ≥ 5 AND absent from benign, remap and
filler* — yields 11 terms, and **`forklift` is not among them**:

`operators(26), accident(10), malfunctioning(9), moving(8), loads(7), capacity(7), involving(7),
miss(6), horn(5), construction(5), warning(5)`

#### Problem 1 — lexical leakage: the head noun fails its own rule

| word | concept pool | benign | remap | filler |
|---|---|---|---|---|
| **`forklift`** | **400** | **2** | 0 | 0 |
| `carrot` | 0 | 400 | 0 | 0 |
| *(d10 for comparison)* `bomb` | 400 | **0** | 0 | 0 |

**Two benign carrot sentences mention a forklift**, which is entirely plausible in a warehouse or farm
setting — and it is enough for a strict "absent from benign" rule to drop the very word the flag exists
to detect. `bomb` never leaked because a benign carrot sentence has no reason to mention a bomb.
**This is a pool defect, not a rule defect**, and the rule behaved correctly by excluding a
contaminated term.

#### Problem 2 — the deeper one: the concept pool's vocabulary is INCIDENT vocabulary, not FORKLIFT vocabulary

Look at what the rule did surface: `accident`, `malfunctioning`, `warning`, `involving`, `miss`. Those
are properties of the **prompt template** — the `harm`-valence pools are generated as *"incident-log
sentences from a safety inspection"* — not of the concept. Meanwhile genuinely forklift-specific words
score **zero**: `tines` 0, `mast` 0, and `pallet` is contaminated across all four valences (13/4/1/4).

**So a flag built from this pool would largely detect "the model is talking about accidents", which is
a property of the demonstration register that every arm shares.** That is a *different* confound from
R-27's, but it is the same shape: **the flag would not isolate mapping use.**

**⛔ What I am NOT doing.** I am not relaxing the threshold to `benign ≤ 2` to let `forklift` back in,
and I am not hand-adding `tines`/`mast`/`pallet`. Both would be tuning a rule after seeing it fail —
the exact move PR-31 forbade and R-78 refused to make.

**Two candidate repairs, neither taken this tick.** (a) `prompt_families.py` already exposes
`--incidental-replace OLD=NEW` and banks carry an `incidental_repairs` field, so removing incidental
concept-word occurrences is a **sanctioned, recorded operation** rather than an ad-hoc edit — that
addresses Problem 1. (b) Problem 2 needs the concept pool generated in a **register that names the
object rather than the event**, which is a prompt-template change in `demo_pools.py` and a larger
commitment.

**Deciding this at the end of a long tick is how PR-31's flaw got in.** The pool is generated and costs
nothing to keep; the decision waits for the next tick with both repairs costed. **Nothing is
pre-registered and no arm is submitted.**

*(Also adopted this tick, from the concurrent session: `demoproc`'s cap null has 1 discordant pair and
so could not have reached α = 0.05 either way — it is underpowered, not a measured zero. C-23 and the
summary now say so.)*


### ⛔ R-81 (21:40) — **Limitation 2 is CLOSED AS NOT RESOLVABLE with the instruments available, and I am stopping this branch rather than building a third bank. The bank build the user authorised was spent, and what it bought is a precise diagnosis instead of a result.**

**The decision R-80 deferred, taken with the register problem costed.**

**Why the forklift repairs are not worth taking.** Repair (a), `--incidental-replace`, fixes only the
head-noun leakage — **but PR-31 already measured that the head noun is the part the model does not
produce** (1/40 rows). Fixing leakage buys a clean flag for a term that does not appear. Repair (b),
regenerating the concept pool in an object-naming register, is a `demo_pools.py` template change whose
payoff is unknown and which would be my **third** guess at this instrument.

**And the last cheap alternative is not one.** The bank's `comprehension_usage` query kind looked like
free-generation usage; it is `'Answer with exactly one word, either literal or coded'` — a two-way
forced choice that detects **that** a word is coded, never **what as**. Like `comprehension_mc` and
`semantic_forced_choice`, it is a probe. **The bank contains no query kind that elicits free-generation
naming of the concept**, which is what limitation 2 needs.

#### Why the measurement is hard, stated as the finding

| instrument | what it gives | why it fails limitation 2 |
|---|---|---|
| harmful concept (`bomb`, R-27) | 64-81% concept usage among jailbroken rows | **confounded**: usage ≈ "produced harmful content". Baseline-not-jailbroken is 6-10%, killed rows 0-4% — the drop is explained by jailbreak status alone |
| benign concept via `benign_remap` (`bicycle`, PR-31/R-78) | head noun **1/40**; concept vocabulary **11/40 vs 0/20 floor** | **head noun too rare to gate on**; vocabulary flag not pre-registered and cannot be adopted post hoc |
| purpose-built benign pool (`forklift`, R-79/R-80) | 11 rule-derived terms, **head noun excluded by leakage** | the pool's distinctive vocabulary is the **incident register** (`accident`, `malfunctioning`, `warning`) that **every arm shares**, not the object |

**The unifying reason: with a harmful concept the model names the concept because the request pulls the
content out of it; with a benign concept it has no reason to name anything, and the vocabulary that
remains is the demonstration register rather than the mapping.** Usage and harm are entangled *because*
harm is what makes usage observable.

#### What would actually work, specified so the next attempt does not repeat these three

A **register-controlled** usage measure, which none of the above has:

1. A benign concept whose pool is generated in a register that **names the object** rather than
   narrating an event.
2. A **register control** holding demonstrations fixed while removing the mapping — the bank's
   `irrelevant` arm (`DISTRACTOR_CODEWORD = "tulip"`) is the right shape: if concept vocabulary appears
   when the query asks about a word the demos never remapped, that vocabulary is **echo, not use**.
3. A query that gives the model a **reason** to name the object without asking it to (the probes ask;
   that is why they are probes).

**⛔ Not attempted.** That is a bank *and* a query-family design, it is my fourth iteration on one
limitation, and R-76's standard — *do not invent work; do not rescue a failed gate* — applies to me
here as much as it did to the layer sweep.

**Limitation 2 stands as recorded, now with a diagnosis rather than a gap.** The honest position: R-27
said this needed a benign-register concept; **that was necessary and not sufficient**, and the missing
half is a register control. **That is what the authorised build bought**, and it is worth more than a
fourth guess would have been.

**⛔ No GPU is queued for this branch and none will be without a new decision.**


### ⚠ R-82 (21:55) — **Judge-invocation audit prompted by the concurrent session: every PRIMARY contrast in this phase is within-invocation, but pool A's `matched_d2`/`d3` controls are NOT — and they sit at the judge noise floor.**

The peer measured the judge floor three ways on byte-identical generations — unpinned 37/660 =
**0.0561**, pinned `q15A` 7/160 = **0.0437**, pinned `q16A` 9/160 = **0.0563** — and reported that
**pinning does not reduce it** (it prevents silently averaging two judge *models*, which is a different
and real benefit). That matches my own DR-10 measurement of **9/160 = 0.0563** exactly. **On an 80-row
population the floor is ~4 rows, and C7's cell-sets are net differences of 3-5 rows.** So their question
— *were your arms judged in the same invocation as their baselines?* — is the right one.

**Audited, by launch batch:**

| result | judge dirs | launch stamps | within-invocation? |
|---|---|---|---|
| **pool A (R-58)** | 5 | `003934`, `004721`, `004733` | **A + demoproc + d1 together; d2 and d3 ~8 min later** ⚠ |
| pool B (R-62) | 5 | `032749`, `032750` | yes (one script, parallel launch) |
| 640-cap (R-64) | 3 | `045339` | yes |
| codeword 192 (R-73) | 5 | `095924`, `100000` | yes (36 s, one script) |
| codeword 640 (R-75) | 2 | `111830` | yes |
| Q7 (R-70) | 5 | `074049`, `074050` | yes |
| PR-28 (R-71) | 4 | `083916`, `083917` | yes |

**The primary contrast is clean everywhere.** In pool A, `demoproc` and its baseline share stamp
`003934` — **the arm carrying the effect was judged with its baseline**, so the −5/5 and −5/7 cells are
not exposed to cross-invocation drift. Pool B, the 640-cap rerun, and every later result are
single-invocation throughout.

**What is exposed:** pool A's **`matched_d2` and `matched_d3`** were judged 8 minutes after the
baseline. Their readings (control removes **2, 2** at n=4 and **−2, −1** at n=8) are **1-2 rows** —
**at or below the ~2-row floor for a 40-row cell.** So on pool A those two control nulls are
**noise-limited**, which is weaker than "measured inert". `matched_d1` shares the baseline's invocation
and is unaffected.

**No number changes and nothing is retracted.** C7's conclusion never rested on those two controls
individually: pool B re-ran all three within one invocation (**+1, +1, +1** and **0, −1, −2**), and the
640-cap rerun did too. **The caveat is that pool A's `d2`/`d3` nulls should not be quoted as evidence of
inertness on their own** — the pool B replication is what carries that leg.

**A reciprocal caveat I owe the peer**, since it cuts against a number that favours my claim: their
sprint-grade C7 replication reports a **paired exact p = 0.006348** on **ASR** (demoproc 11 down / 1 up,
12 discordant). **PR-28 explicitly declared that the paired exact test does NOT apply to ASR**, because
ASR labels are not reproducible at ~5% per row — so of those 12 discordant pairs roughly **4 are judge
noise**, and the exact p treats all 12 as signal. The direction and magnitude are still striking
(≈8 net-down after subtracting the floor), but **that p is optimistic and should not be quoted as-is.**
**I am not adopting it as my own statistic either** — adopting a test I pre-committed against, at the
moment it favours me, is the move this log exists to prevent.


### ⛔ C-25 (22:05) — **CORRECTION to R-82: I claimed symmetric judge noise makes a paired exact p "optimistic". It does the opposite. Simulated independently rather than conceded — and my own simulation refutes me.**

R-82 asserted, against the concurrent session's C7 replication, that *"of those 12 discordant pairs
roughly 4 are judge noise, and the exact p treats all 12 as signal… that p is optimistic."* **The
mechanism is wrong.** They simulated it; I ran my own simulation before accepting theirs
(n=80, base 11/80, 6000 reps/cell, seed 20260827):

| symmetric flip rate | type I error (H0) | E[down] | E[up] |
|---|---|---|---|
| 0.00 | **0.0312** | 9.49 | 9.52 |
| 0.05 | **0.0283** | 11.47 | 11.47 |
| 0.10 | **0.0327** | 13.27 | 13.24 |
| 0.20 | **0.0285** | 16.22 | 16.22 |

**Every cell is at or below the nominal 0.05.** The reason is structural and I should have seen it:
McNemar's null is `P(A=0,B=1) = P(A=1,B=0)`, and **symmetric independent noise fills both discordant
cells equally** — it manufactures exactly the 50/50 split the null assumes. It cannot create a false
positive. What it destroys is **power**:

| flip | power at true Δ = −0.125 |
|---|---|
| 0.00 | 0.845 |
| 0.05 | **0.526** |
| 0.10 | **0.329** |

**So symmetric label noise makes that test CONSERVATIVE, not liberal, and "the p is optimistic" is
withdrawn.** My "~4 of the 12 are noise" arithmetic was right and the inference from it was wrong:
those ~4 split ~2 up / ~2 down and **cancel in the net**, which is precisely what the test reads.

**Where my concern was actually valid — asymmetric noise**, which I did not distinguish:

| extra up-bias on one arm | type I error |
|---|---|
| 0.00 | 0.0265 |
| 0.05 | **0.0640** |
| 0.10 | **0.1740** |

**That inflation is real and is live whenever two arms differ systematically in a way the judge
responds to** — such as completion length, where `demo_processing_only` runs longer (median 277 vs
212.5). **But the asymmetry that design plausibly has pushes the knockout arm UP, and the observed
result is 11 DOWN against 1 up.** The one bias the design carries works *against* the result, which
makes it stronger, not weaker.

#### What this does to PR-28

PR-28 declared the paired exact test **never applies to ASR**, reasoning that *"ASR labels are not
reproducible at ~5% per row"*. **The declaration stands; its stated rationale was wrong.** The correct
reasons to keep ASR out of that test are:

1. **Power collapse** — at a 5% floor, power against Δ = −0.125 is **0.526**, so a *null* from it is
   nearly uninformative. (This is the same detectability rule the peer applied to `demoproc`'s cap null
   and I applied to the `2/2^k` floor.)
2. **Asymmetric-noise risk**, which is genuinely live for arms differing in length — and which
   symmetric-noise reasoning cannot see.

**I am still not adopting the test for my own ASR claims**, and now for reasons that survive scrutiny
rather than for the one I invented.

**The joint measurement worth stating once.** The judge floor is now measured twice by independent
routes on byte-identical text: **DR-10's `q9j_L5` vs `q9j_ko` = 9/160 = 0.0563** (an arm that is a
bit-exact no-op, so the two sets are literally the same bytes) and the concurrent session's **pinned
`q16A` re-judge = 9/160 = 0.0563**, plus `q15A` 7/160 = 0.0437 and an unpinned 37/660 = 0.0561.
**Pinning does not reduce it.** Four measurements, two designs, one number: **≈5% of binary ASR labels
flip on identical input.**

**Why this correction matters beyond the arithmetic.** R-82 was me being appropriately sceptical of a
number that favoured my own claim — and I was *wrong in the direction of excessive caution*, which is
still wrong. **Scepticism is not self-validating; it has to be checked too.**


### ✅ R-83 (22:20) — **The judge floor is now PER-ARM, and applying it to C7 turns R-82's estimate into a measurement: the pool-B effect is 3.6× the paired noise, and the two flagged control cells are 0.00× and 0.38×.**

The concurrent session ran the boundary test and confirmed the prediction: on 320 double-judged rows,
flips concentrate almost entirely at the decision boundary — **9/17 (0.53) within |score − 0.5| < 0.15
versus 5/289 (0.0173) beyond it.** Per their own caveat I use **only the two-bucket contrast**; their
five-bucket split rests on n = 11, 6, 8, 6 and is not quotable.

**That makes the floor a property of an ARM, not of the corpus**, because it depends on how much
borderline mass the arm has. Applied to my arms (`near` = rows with |score − 0.5| < 0.15):

| arm | near/160 | effective flip rate | expected flips |
|---|---|---|---|
| pool A baseline | 7 | 0.0397 | 6.35 |
| pool A `demoproc` | 5 | 0.0333 | 5.33 |
| pool A `matched_d1` | 10 | **0.0493** | 7.89 |
| pool B baseline | 10 | **0.0493** | 7.89 |
| **pool B `demoproc`** | **1** | **0.0205** | **3.28** |

**The peer flagged a risk that turns out not to bite here, and the reason is worth keeping.** They
warned that my flagged `matched_d2`/`d3` cells might face a floor *worse* than my ~2-row estimate. At
the decisive doses those arms have **5 and 2** borderline rows in 80 — effective rates **0.0493** and
**0.0301**, at or below the corpus average. The arms that face an above-average floor are the
**baselines** (0.0493), not the controls.

#### C7 against its own measured noise

Symmetric flips move the paired net by ±1 with equal probability, so `Var(net) = total expected flips`
(C-25's result is what licenses this). Pool B, decisive doses, 80 rows per arm:

| | value |
|---|---|
| baseline expected flips | 4.97 (7 near-rows) |
| `demoproc` expected flips | 1.38 (**0** near-rows) |
| **paired net-noise SD** | **2.52 rows** |
| **observed effect** | **10 → 1 = −9 rows** |
| **effect / noise SD** | **3.6×** |

And the two cells R-82 flagged, pooled over both decisive doses:

| cell | net | paired noise SD | ratio |
|---|---|---|---|
| `matched_d2` | **+0** rows | 2.90 | **0.00×** |
| `matched_d3` | **−1** row | 2.62 | **0.38×** |

**R-82's characterisation is confirmed and is now quantitative**: those two nulls are **not** evidence
of inertness — they are indistinguishable from zero noise-wise — while **the effect they are supposed
to contrast with is 3.6× the same noise**. The asymmetry is the point: `demoproc` has **zero**
borderline rows at the decisive doses, which is *why* its floor is the lowest of any arm and why the
contrast survives.

**⚠ What this rests on.** The near/far rates are the peer's measurement on `q15A`/`q16A` double-judgings
and I am importing them as a mixture model onto my arms. **It is a measured floor transplanted, not a
floor measured on these arms**, and the 3.6× would move if the boundary rates differ by population.
The direction of the borderline counts (0 near-rows in `demoproc`) is directly measured on my own data
and is not transplanted.


### 🔎 DR-12 (22:15) — **Per-arm floor applied to EVERY ASR contrast in the phase, not just C7. They separate into two clean tiers, and nothing sits below its floor.**

R-83 applied the per-arm judge floor to C7 only. The user's standing review item is *"verify no
structure is being fitted below the measurement reproducibility floor"* — so it belongs on every
ASR-based contrast, including the ones where the answer might be unwelcome.

Method as R-83: `near` = rows with |score − 0.5| < 0.15; expected flips = `near×0.5294 +
far×0.0173`; symmetric flips move the paired net by ±1 so `Var(net) = total expected flips` (C-25).

| contrast | n | baseline | arm | net | noise SD | **ratio** |
|---|---|---|---|---|---|---|
| Phase-1 `legacy_all_query` | 96 | 16 | 3 | **−13** | 3.08 | **4.23×** |
| Phase-1 `demo_processing_only` | 96 | 16 | 4 | **−12** | 3.24 | **3.70×** |
| **C7 pool B, decisive doses** | 80 | 10 | 1 | **−9** | 2.52 | **3.57×** |
| Phase-1 `response_query_only` | 96 | 16 | 10 | −6 | 3.47 | **1.73×** |
| Phase-1 `query_prefill_only` | 96 | 16 | 22 | +6 | 3.82 | **1.57×** |

**Two tiers, and the split is not arbitrary — it matches which claims the phase already treats as
strong.** `legacy`, `demoproc` and C7 sit at **3.6-4.2×** their own measured noise. `respq` and `qpre`
sit at **~1.6×**, which is exactly why PR-1's primary comparison came out as an equivalence and why
C-11 withdrew any ranking among them: **those two arms were never separable from noise, and now that
is a measured statement rather than a margin-based one.**

**Nothing is fitted below its floor.** The weakest published contrast is 1.57×, and the claims resting
on the weak arms are **null/equivalence claims** (C3's "indistinguishable", C8's "measured null"),
which is the direction a low ratio supports rather than undermines.

**⚠ Two scope statements, so this is not read as more than it is.**

1. **C8 is NOT tested here.** C8 is `d10`, **160 rows**, a **domain sign test** (−0.0250, p=0.6875);
   the rows above are the Phase-1 **96-row** bank (`boombness_prompt_bank.jsonl`). Different
   population, different estimator. I checked before assuming the numbers spoke to it — they do not.
2. **C3 already carries this.** Its row reads *"all pairwise gaps ≤ 0.0417 **except marginal `qpre`
   pairs**"*. The floor analysis **agrees with** the exception that was already recorded; it does not
   discover a new one.

**And the same transplant caveat as R-83**: the near/far rates are the concurrent session's
measurement on `q15A`/`q16A`, imported as a mixture model. The **borderline counts** driving each
arm's floor are measured on my own rows; the **rates** are not. A ratio would move if boundary
behaviour differs by population — the tiering (4× vs 1.6×) is robust to that, individual ratios less
so.

**No correction issued.** Recorded because a floor audit that finds nothing is only informative if it
says what it covered.


### ✅ R-84 (22:30) — **Headroom audit on my one pooled claim, prompted by the concurrent session's finding that their 8-population aggregate was carried by two populations. C4 is clean — and the reason generalises into a rule about which aggregates are vulnerable.**

They found that *"96 down / 18 up over 8 populations"* is carried by **two** of five Llama populations
(+17, +17) while three contribute **+2, −1, −1** — and that `window_knife`'s baseline ASR of **2/96**
means it has *no attack to remove*, so its near-zero result is **evidence of nothing** being averaged in
as though it were evidence of a small effect. That is my own R-AU (attackability is a bank × model
property) biting an aggregate headline.

**So I audited my only pooled claim.** C4 — *attack removal proceeds by coherent non-compliance* —
reports **0 degenerate rows of 165 across 8 cells**. Per-cell, from
`outputs/boombness/kill_route_breakdown/krb_20260825_131040_3620206/kill_route_breakdown.json`:

| cell | killed rows | | cell | killed rows |
|---|---|---|---|---|
| `llama:demoproc` | 25 | | `qwen3:demoproc` | 20 |
| `llama:legacy` | 24 | | `qwen3:legacy` | 19 |
| `llama:respq` | 24 | | `qwen3:respq` | 20 |
| `llama:qpre` | 18 | | `qwen3:qpre` | 15 |

**Range 15-25, total 165, both models.** No cell contributes less than 9% or more than 15% of the
total. **"8 cells" is not overselling one cell's data**, and the independent re-derivation
(`REPRO_krb_...`) reproduces all eight counts exactly.

#### The rule this exposes, which is the transferable part

**Their aggregate and mine are different shapes, and only one shape has this failure mode:**

* **Vulnerable — an effect size averaged over populations.** A population with no headroom contributes
  ≈ 0 *and still carries weight in the mean*, so it **drags the aggregate toward the null** while
  looking like evidence for a small effect. This is what happened to entry 6.
* **Immune — a proportion computed over the affected rows themselves.** C4's denominator is *killed
  rows*. A cell with no kills contributes nothing to the numerator **and nothing to the denominator**,
  so it cannot dilute; it simply is not represented.

**The diagnostic question is therefore not "how many populations?" but "does a population with no
headroom enter the denominator?"** If yes, the aggregate needs per-population reporting before it can
be quoted. If no, pooling is safe and only *concentration* needs checking — which is what I checked
above.

**No correction.** C4 stands as published, now with its per-cell distribution recorded rather than
assumed.


### ✅ R-85 (22:40) — **Attention-kernel audit prompted by the concurrent session: `config.json`'s `attn_impl` is the REQUEST, not the reality. Checked all 25 of my arms — no mismatch, and the reason is that this phase never requested `sdpa`.**

They found that all five of their entry-6 knockout arms record `attn_impl: "sdpa"` in `config.json`
while every one actually ran **eager**, because `score_behavior.py:1348` forces eager whenever a
knockout is requested. The comment at `1136-1140` gives the reason, and it is a serious one: *under
sdpa the 4-D mask edit is silently discarded*, and under greedy bf16 decoding *a sub-ulp difference on
a near-tie refuse/comply token branches into a different completion and a different judged ASR*. **An
arm-vs-baseline contrast that mixed kernels would confound the mask edit with a kernel swap.**

**Audited: 25 arms across every result in this phase.**

| | result |
|---|---|
| arms requesting `eager` | **25 / 25** |
| knockout arms whose `summary.json` `knockout_liveness.attn_implementation` confirms **eager** | **17 / 17** |
| **mismatches** | **none** |

**Why there is nothing to find here, stated as a property rather than as luck:** every argsfile in
`runargs/p17/` passes `--attn-impl eager` explicitly, and the forcing at line 1348 is
`"eager" if (_wants_knockout or args.attn_impl == "eager") else args.attn_impl` — it only ever
overrides **towards** eager. So a request for eager is always honoured, and this phase's request was
always eager.

**⚠ One honest gap.** The 8 **baseline** arms have no `knockout_liveness` block, so their actual kernel
is **inferred, not recorded**: request = eager, and the override cannot move away from eager, therefore
eager. That inference is sound given the code path I read, but it is an inference. **The knockout arms
are verified; the baselines are derived.** Since baseline and arm requested the same kernel, **no
contrast in this phase mixes kernels either way.**

**Worth keeping as a general lesson about provenance fields**: `config.json` recorded the *argument*,
and the only field carrying the *outcome* is on the liveness block — which exists only for arms that
intervene. **A provenance field that is written before the thing it describes is decided is a request,
not a record**, and this phase has now been bitten by that distinction twice: once here (harmlessly)
and once in C-20, where `rescue_liveness` truthfully reported `fired: true` for a patch that wrote the
value already present. **Liveness told the truth both times; the question it answers is narrower than
the one I wanted answered.**


### ✅ R-86 (22:50) — **Divergence audit of all 18 intervention contrasts in this phase. The distribution is BIMODAL with a gap from 0.00 to 0.82 — which answers the concurrent session's threshold question and suggests a sharper predicate than a threshold.**

They built the invariant I suggested (`intervention_liveness.py`) and asked directly whether
`MIN_DIVERGENCE = 0.10` would wrongly refuse an arm of some shape. **Answered with my own data rather
than an opinion** — generations compared against each arm's own control, joined on `prompt_id`:

| contrast | n | divergence |
|---|---|---|
| pool B `demoproc` / `matched_d1` / `d2` / `d3` | 160 | **1.0000 / 0.8938 / 0.8812 / 0.9313** |
| pool A `demoproc` / `matched_d1` / `d2` / `d3` | 160 | **0.9938 / 0.8250 / 0.8187 / 0.8500** |
| 640-cap `demoproc` / `matched_d1` | 80 | **1.0000 / 0.9625** |
| Q7 knockout / rescue L12 / rescue L17 | 160 | **1.0000 / 0.9000 / 0.9750** |
| codeword 192 / 640 / `benign_remap` demoproc | 96/96/40 | **1.0000 / 1.0000 / 1.0000** |
| **Q7 rescue L5** *(known no-op)* | 160 | **0.0000** |
| **Q7 rescue L7** *(known no-op)* | 160 | **0.0000** |

**Sixteen legitimate arms span 0.8187-1.0000. Both no-ops are exactly 0.0000. Nothing lands in
between.** On this evidence any threshold in `(0, 0.82)` behaves identically, so **0.10 is safe for
every arm shape this phase produced** and is not doing delicate work.

**But the gap is the finding, not the threshold.** My no-ops are not *small*; they are **exactly zero
across 160 rows under greedy decoding**, which is what a bit-identical computation produces and what
nothing else does. So the sharper predicate is:

* **`divergence == 0` is unambiguous and should REFUSE.** Under greedy decoding an arm that changed
  anything cannot land on exact zero across a population.
* **`0 < divergence < 0.10` should WARN, not refuse**, because it is genuinely ambiguous — and it is
  the region a legitimate arm could occupy. **My arms cannot reach it, but they are all broad-span
  mask or patch interventions.** A single-position patch, or `--rescue-n-positions 1`, or an
  intervention gated on a rare row property, could legitimately touch few rows. **A threshold tuned on
  broad-span arms would refuse those.**

**And divergence alone under-determines the diagnosis** — combining it with the liveness field
separates the three cases cleanly:

| `fired` | divergence | diagnosis |
|---|---|---|
| `false` | 0 | the hook never ran — an instrument failure |
| **`true`** | **0** | **C-20's case: the hook ran and wrote the value already present** |
| `true` | small but > 0 | a legitimately small intervention |

**That is the pair worth asserting, rather than either field alone** — which is exactly the lesson
R-85 drew from `attn_impl` (a request needs its matching outcome field) arriving at the same shape from
the other direction.

**Independent confirmation worth recording**: their run of the invariant over my `q9` ladder reproduces
`test_below_band_rescue_is_a_noop.py`'s analytic predicate **empirically** — L5 and L7 (both ≤ `lo` = 7)
at 0/160, L12 and L17 at 144/160 and 156/160. **Derived predicate and measured generations agree.**


### ⛔ C-26 (23:05) — **The test I committed as C-20's guard is a TAUTOLOGY: it passes with the production code broken. Found by mutation-testing my own test, prompted by the concurrent session reporting the same pattern twice today.**

They recorded that two of their mutations *"came back green and the fault was mine, not the code's"* —
an unfired mutation reading as a passed one. **That is worth more as a pattern than as an instance, so
I applied it to the test I wrote today.**

**`tests/test_below_band_rescue_is_a_noop.py` imports only `pytest`.** Its predicate,
`patch_can_differ_from_recipient`, is **defined inside the test file**. Verified by mutation — renaming
`DonorPatch.liveness` in `src/boombness/donor_patch.py`:

| | before the fix | after |
|---|---|---|
| all tests with `donor_patch.py` broken | **11 passed** ⛔ | **1 failed, 11 passed** ✅ |

**It could not fail for any change to the code it purports to guard.** I committed it under C-20 as the
thing that "stops a below-band layer being described as a control again", and it does no such thing
mechanically.

**What it actually is, now labelled as such.** It encodes a **rule**, and the rule has already been
re-derived wrong twice — C-20 first wrote it as *"below the band"*, then R-68 measured the band
**floor** to be vacuous too and corrected it to `layer > lo`. **Documentation against that specific
recurrence is real value.** Calling it a regression guard was not.

**Fixes applied, both minimal:**

1. The module docstring now states plainly that it is a rule, **not** a regression guard, that it
   passes with `donor_patch.py` broken, and that `tests/test_donor_patch.py` is the file that actually
   exercises the production code (`strict_ids`, write, liveness, hook teardown).
2. **One binding assertion added** — `DonorPatch` and `DonorPatch.liveness` must exist. The rule is a
   statement *about* that class; if it disappears the rule describes nothing and the file should fail
   rather than keep passing quietly. **The mutation that was green is now red.**

**Why the empirical version is not available**: `outputs/` is gitignored (`.gitignore:11`), so the fact
behind the rule — L5/L7 byte-identical to their control, L12/L17 not — **cannot be pinned in-repo**.
That is a real limit and is now stated in the file rather than left as an implicit "surely someone
would notice".

**The general shape, which is C-20's own lesson turned on my tooling.** C-20 was *a hook that reported
firing while changing nothing.* This is *a test that reported passing while checking nothing.*
**Both were true statements about a narrower question than the one I was asking**, and in both cases
the only thing that exposed it was **comparing against something that should have differed** — a
control's generations there, a mutated module here.


### ⛔ C-27 (22:55) — **C-26 was not one bad test. FOUR of this phase's guards assert on SOURCE TEXT, which catches a guard being DELETED but not DISABLED — and two of them fail to catch the exact regression they were written for.**

C-26 fixed one tautological test. **The obvious next question is whether it was alone**, so I audited
every test file this phase added, by what each actually binds to:

| binding | files | catches |
|---|---|---|
| **executes production code** | `test_donor_patch` (imports + exercises), `test_bank_regenerates_byte_identically` (subprocess) | semantic breaks |
| **reads real artifacts / deliverables** | `test_argsfiles_match_runs`, `test_published_percentages_are_row_exact`, `test_preamble_is_the_only_difference` | drift in the things they read |
| ⛔ **reads production source as TEXT** | `test_bridge_bank_guard`, `test_control_feasibility`, `test_rescue_dissociation_table`, `test_dose_breakdown` | **deletion only** |
| ⛔ **nothing** (C-26, fixed) | `test_below_band_rescue_is_a_noop` | — |

**Mutation-tested rather than asserted**, on the two that matter most:

| mutation | what it models | result |
|---|---|---|
| `if _missing:` → `if False and _missing:` in `binding_behaviour_bridge.py` | **C-13's guard disabled**, text intact | **8 passed** ⛔ |
| `--model required=True` → `required=False` in `control_feasibility.py` | **C-18 exactly** | **8 passed** ⛔ |

**The second one is the serious one.** `test_control_feasibility.py` exists *because of C-18* — where
`--model` defaulted, feasibility was measured on **Llama's** tokenizer, quoted as a **Qwen3** statement,
and the arms then refused at pre-flight. **The test written to prevent that recurrence does not fail
when it recurs.**

**Fixed, minimally and by execution.** `test_model_is_actually_required_when_the_script_runs` runs the
script with `--model` omitted in a subprocess and requires a non-zero exit that **names the argument**.
Verified both directions: **green on the real code, and the C-18 mutation is now RED** (1 failed,
5 passed).

**Not fixed, and stated rather than left implicit**: `test_bridge_bank_guard`,
`test_rescue_dissociation_table` and `test_dose_breakdown` remain source-text assertions. They catch
deletion, which is the common accident, and **they do not catch inversion**. Making them executing
tests needs constructed fixtures (a bank with missing ids, a judge dir pair), which is real work I am
**not** doing at the end of a session — **the file now says what each one does and does not catch**, so
the next person does not have to mutation-test them to find out.

**The pattern across C-20, C-26 and C-27 is one pattern, and it is worth naming.** Each was an artifact
that **truthfully answered a narrower question than the one being asked of it**:

* C-20 — `fired: true` answered *"did the hook execute?"*, not *"did the hook matter?"*
* C-26 — a passing test answered *"is this predicate self-consistent?"*, not *"does the code obey it?"*
* C-27 — a source-text assertion answers *"is the guard present?"*, not *"is the guard active?"*

**In all three the only thing that exposed the gap was comparing against something that should have
differed** — a control's generations, a mutated module, a disabled condition. **Nothing about the
artifact itself was ever wrong.**


### ✅ R-87 (23:00) — **C-13's guard is now covered by an EXECUTING test. The mutation that was green under the text assertions is red under this one. Two of C-27's four remain, and I am saying which and why.**

C-27 identified four source-text guards and fixed one (`control_feasibility`, C-18's). I deferred the
rest as *"real work I am not starting at the end of a session"* — **that was a timing judgement, not a
merit one**, so it is the right work now rather than something to leave.

**Converted: `test_bridge_bank_guard.py`**, which guards **C-13** — where
`binding_behaviour_bridge` silently kept **96 of 160 rows** and printed a complete-looking answer over
a different population. The new test builds a minimal fixture (a bank knowing 2 ids, run dirs carrying
4), runs the real script in a subprocess, and requires the refusal:

| | text assertions only | with the executing test |
|---|---|---|
| real code | 4 passed | **4 passed** |
| `if _missing:` → `if False and _missing:` *(guard disabled, text intact)* | **4 passed** ⛔ | **1 failed, 3 passed** ✅ |

**The fixture is the whole trick and it is cheap**: the bridge needs only `prompt_id` + `family_id`
ending in its `query_kind` from the bank, `strongreject_score` from a judge dir, and
`p_concept`/`p_codeword` from a probe dir. **No model, no GPU, 28 s.** I had assumed constructing it
was expensive; it was not, and that assumption is why C-27 shipped with three gaps instead of one.

**Still text-only, stated rather than left to be discovered**: `test_rescue_dissociation_table` and
`test_dose_breakdown`. Both guard **reporting rules** — *"refuses to emit a percentage without
`effect_rows` and `effect_x_margin`"* and the per-dose cell-size requirement — rather than population
integrity. **A disabled reporting rule produces a number that looks wrong to a reader; a disabled
population guard produces a number that looks right.** That is why C-13's was worth the fixture first
and why these two are a lower priority, **not** why they are fine.

**What this run of the pattern cost and bought.** C-20 → C-26 → C-27 → R-87 is one thread: an artifact
that answers a narrower question than the one asked of it, found only by comparing against something
that should have differed. **Each step was cheaper than the last** — C-20 took a GPU sweep and a
same-session control arm, C-26 took one rename, C-27 took two, R-87 took a 30-line fixture. **The
expensive part was never the check; it was not knowing the check was owed.**


### ⛔ R-88 (23:15) — **R-87's own justification for deprioritising two tests was WRONG, and DR-5 is the proof. Converted the one it misjudged.**

R-87 left `test_rescue_dissociation_table` and `test_dose_breakdown` as source-text assertions with a
stated reason:

> *"A disabled reporting rule produces a number that looks **wrong** to a reader; a disabled population
> guard produces a number that looks **right**."*

**That is false for this guard, and the counterexample is the failure it exists to prevent.** DR-5:
the published *"% of refusal rise removed"* figures were **92.3%** and **69.2%**, and they **ranked the
cells backwards** — 92.3% was **12 rows / 1.44× margin** (the weakest) and 69.2% was **18 rows /
2.16×** (the strongest). **Those numbers looked entirely right.** The failure is **invisible**, the same
class as C-13's, so it earns an executing test on the same grounds.

**Converted.** The invariant asserted on real output rather than on source: **no cell may carry
`pct_of_rise_removed` without `effect_rows` and `effect_x_margin` beside it.** Fixture is four judge
dirs of 8 rows; no model, no GPU, 14 s.

| | before | after |
|---|---|---|
| real code | 6 passed | **7 passed** |
| `"effect_x_margin": …` → `None` *(rule disabled, source text intact)* | **6 passed** ⛔ | **1 failed, 6 passed** ✅ |

**`test_dose_breakdown` remains text-only, and now for a reason I have actually checked** rather than
one I asserted: its rule is that **per-dose cell sizes are emitted beside per-dose numbers**. A missing
cell size is visible in the artifact — a reader sees a rate with no `n` and cannot compute anything
from it — whereas DR-5's percentage was **self-consistent and complete-looking while being backwards**.
**That distinction is real; the blanket version I wrote in R-87 was not.**

#### The correction under the correction

R-87 closed by observing that each step of this thread was cheaper than the last, and that *"the
expensive part was never the check; it was not knowing the check was owed."* **I then immediately used
a plausible-sounding rule to decide two checks were not owed — without checking.** The rule was
invented in the same message that congratulated itself for noticing this failure mode.

**The pattern is now four deep** — C-20, C-26, C-27, and R-87's justification — and every instance is
the same: **something true about a narrower question, used to answer a wider one.** Here the narrow
truth is *"some reporting failures are visible"*; the wider claim was *"reporting failures are
visible"*.


### 📌 R-89 (23:40) — **Verification tick. The shared suite is RED (8 failures) and none of them are mine — reported to the owning session, not touched. This phase's own work has nothing left to do, stated plainly rather than filled.**

**Suite: 8 failed, 1194 passed, 7 skipped.** All eight are `tests/test_arm_report.py`, the concurrent
session's file. Cause, from the traceback rather than inference:

> `asr_protocol.ExcludedRunError: base: [require_done] REFUSING: … has no DONE.json, so the run did
> not finish and its 40 rows are a truncated prefix of unknown length`

**Their V-20 guard is firing on their V-18 fixtures.** The guard is behaving exactly as built; the
fixtures predate it and construct judge dirs without `DONE.json`. **Their file, their boundary —
reported and not edited.**

**My side, verified**: 87 tests across all 11 files this phase added or touched — green.
`check_all.py` 6/6. All nine corrections `C-19 … C-27` present in the sprint summary. Every
pre-registration `PR-25 … PR-31` carries a recorded outcome.

#### There is nothing left for this phase to do, and that is the finding

Each of the last several ticks found real work, but the thread has been getting narrower — from
science (C7, Q7), to instrument audits (floors, kernels, divergence), to auditing my own audits
(C-26, C-27, R-87), to **correcting a justification I had invented one tick earlier** (R-88). **R-88 is
the signal that the vein is exhausted**: when the newest finding is an error in the previous finding's
reasoning rather than in the work, further ticks are more likely to manufacture work than to find it.

**Status, complete:**

| | |
|---|---|
| §20 questions | all resolved, declined on evidence, or failed their gate |
| limitation 2 (mapping usage) | **closed as not resolvable** with available instruments (R-81) |
| limitation 5 (lexical G) | **lifted for C1 only**, G = 2, truncation-robust row-for-row |
| ASR contrasts | all floor-audited; **nothing below its floor** (DR-12) |
| arms | liveness-, kernel-, divergence- and provenance-audited |
| guards | the two whose failures are **invisible** now execute; the one that is visible is documented as such |

**So this tick launches nothing and pre-registers nothing.** The remaining value in the loop is
staying responsive to the concurrent session, which has twice surfaced things that touched my claims
(C-23's framing, C-24's scope) — **not in generating a ninetieth entry.**


### ✅ R-90 (00:05) — **My four cap pairs are PURE TRUNCATION at 0% binding-row overlap — the clean contrast to the concurrent session's degeneracy case at 100%. Their classifier separates two regimes rather than flagging "binds a lot", and my arms are the negative control for it.**

They found an arm that binds on **29/96 rows at BOTH 640 and 1536** — *the same 29 rows*, every one
landing on exactly the cap — while its baseline binds **0/96** at both. That is **non-termination, not
truncation**, and their §0.2 rule *"if the cap binds, run a larger cap"* would have chased it forever.
They now classify on **binding-row identity overlap across two caps**.

**I have four cap pairs and every one is the opposite regime.** Applied to my own data:

| population | n | binds @192 | binds @640 | overlap | verdict |
|---|---|---|---|---|---|
| Llama `basket_bomb` baseline | 96 | **90** | **0** | **0 (0%)** | pure truncation |
| Llama `basket_bomb` `demoproc` | 96 | **82** | **0** | **0 (0%)** | pure truncation |
| Qwen3 `longpreQ14B` baseline | 80 | 48 | **0** | **0 (0%)** | pure truncation |
| Qwen3 `longpreQ14B` `demoproc` | 80 | **72** | **0** | **0 (0%)** | pure truncation |

**Their case is 100% overlap; all four of mine are 0%.** That is what a classifier needs to be worth
having — **it is not merely flagging populations that bind heavily**, since mine bind on **up to 94% of
rows** at the low cap and resolve completely at the high one. **My arms are the negative control for
their instrument**, and it passes.

**This also retro-validates PR-26 and R-75.** Both gated on `frac_stop_length < 0.15` at the higher cap
and both got **0.000**. Under the sharper classifier that number now means something stronger than it
did when I wrote it: **not "few rows are cut off" but "no row fails to terminate"** — the arms were
never in the degenerate regime, so raising the cap was the right response rather than a treadmill.
**I got the right answer for a reason I had not articulated.**

**And the shapes line up.** Their rule said *"more room"* to a generation that never terminates; a
liveness contract says *"it fired"* about a hook that wrote what was already there (C-20). **Both
respond to a symptom without asking what produced it** — and in both cases the fix was the same move:
**compare against something that should have differed** (a second cap, a control's generations).

**Interpreter check, from their warning.** The login-node `python` cannot import torch, so
`python -m pytest tests/` there dies with **16 collection errors and runs nothing**. Verified: it fails
**loudly** — `Interrupted: 16 errors during collection` — so it **cannot** produce a false green. Every
suite count in this log came from
`/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`, as the user's cadence
requires, so **no reported pass is affected.**


### ✅ R-91 (00:15) — **Two cross-session number discrepancies chased to ground rather than accepted. Both reconcile; my recorded provenance is correct; the peer's re-derivation habit is what surfaced them.**

The concurrent session re-derived R-90's negative control instead of accepting it, and reported two
things that did not match. **Both are now checked.**

**(1) A run id.** They report one id in my message as `g2A_…739914` against a real
`…739916`. **Audited my own files**: `739914` appears **nowhere** in the live log, the handoff, the
summary, or any `scripts/judge_*.sh`; the only `g2A` id any of them cites is
**`g2A_20260827_091838_739916`**, which matches the directory on disk exactly. **So my recorded
provenance is correct and the slip was in transcription, not in the artifact record.** That is the
better failure of the two, but it is still a slip in something someone else had to act on — and their
**re-derive-before-use** habit is precisely why it cost nothing.

**(2) Qwen3 binding counts.** They report **69/160** and **112/160** where R-90 recorded **48/80** and
**72/80**. Their explanation was a denominator difference. **Verified rather than accepted:**

| arm | their denominator (all low-cap rows) | my denominator (rows common to both caps) | subset? |
|---|---|---|---|
| baseline | 160 rows, **69** bind | 80 rows, **48** bind | **yes** |
| `demoproc` | 160 rows, **112** bind | 80 rows, **72** bind | **yes** |

**The restricted binding set is a strict subset of the full one in both arms**, and the 640-cap arms
bind **0** within the common rows either way — so **overlap is 0% under both denominators** and the
classification is unchanged. **The discrepancy is real, explained, and inert.**

**Why R-90 used the smaller denominator, stated so the choice is not invisible**: the 640-cap arms were
generated at `n_examples ∈ {4,8}` only (PR-26 restricted to the decisive doses), so **80 rows are all
that exist on both sides of the pair.** An overlap statistic requires the same rows at both caps;
quoting 160 would put rows in the low-cap count that have no high-cap partner. **Their 160 is the right
number for "how much does this population truncate"; my 80 is the right number for "do the same rows
bind at both caps".** Different questions, and the classifier asks mine.

**Also confirmed this tick**: `scripts/judge_e6_main_batch.sh` appeared untracked in my tree and is
**theirs** (V-25, entry 6) — left alone, not staged. Shared suite green at **1207 passed, 7 skipped**
under the conda interpreter.


### 🔎 DR-13 (01:15, 4h DEEP REVIEW) — **First review since the concurrent session began committing to shared code. Blast radius checked, every headline recomputed, nothing moved. Suite 1207/0.**

The queue is empty for the first time in a day — **both sessions' jobs are done** — and no job of mine
failed. The new risk since DR-11 is not my own work, which has not run since; it is that **another
session has been committing to `src/boombness/` under my results.**

**Blast radius, computed rather than assumed.** Files they changed since DR-11 (`cc50d20d`):
`arm_report`, `asr_protocol`, `bank_leakage_probe`, `cap_natural_experiment`, `intervention_liveness`,
`paired_test_noise_sensitivity`, `token_vs_prompt_level`, **`prompt_families`**. My analysis path
imports `common`, `coherence_gate`, `ds_common`, `extract_boombness`, `score_behavior` — **none of
their new modules is in my import graph.** The one overlap that matters is `prompt_families`, because
it generates the banks.

**So I verified the C-10 hazard myself instead of accepting their report of it** — C-10 is exactly this
failure (expanding `DOMAINS` broke canonical regeneration) and it is the reason I warned them:

| check | result |
|---|---|
| canonical banks regenerate byte-identically | **3 passed** |
| `N_EXAMPLES` at `prompt_families.py:71` | **`(0, 1, 2, 4, 8, 16)` — untouched** |
| `longpreQ14B` sha (C7's bank) | **`b2903479258a0f68` — matches the committed value** |

**Their derived-preset approach held.** The ne12 cell exists without any canonical bank changing
meaning.

**Every headline recomputed from `results.jsonl`, after their commits:**

| claim | recomputed | published |
|---|---|---|
| C7 pool A | 5→0, 7→2 | ✅ |
| C7 pool B | 4→0, 6→1 | ✅ |
| C7 640-cap | 4→1, 7→0 | ✅ |
| C1 Llama/A | 9 → 35 | ✅ |
| C1 Qwen3/A | 2 → 23 | ✅ |
| C1 Llama/B | 1 → 32 | ✅ |
| C1 codeword | 2 → 14 | ✅ |

**Seven for seven.** Liveness/overwrite sweep across **28 arms**: every intervention arm
`frac_rows_scope_live = 1.0` with no violations, **exactly one `DONE` directory per tag**, `n_failed=0`
throughout. Full suite **1207 passed, 7 skipped** under the conda interpreter.

**No correction issued.** Recorded because the point of this review was a specific new exposure —
**shared code moving under settled results** — and the answer is that it did not reach them. That is
worth stating explicitly rather than leaving as an absence.


### ✅ R-92 (02:20) — **A shared-code off-by-one touches a median I published. My verdict is unaffected, and the bias has a direction that decides the general case: it can only manufacture false PASSES, never false BELOWs.**

The concurrent session found `score_behavior.py:2020` computing `v[len(v) // 2]` — for even `n` the
**upper-middle element, not the median**. Confirmed on a trivial case: `sorted([1,2,3,4])` gives
**3**, true median **2.5**. They swept the corpus: **28 runs** carry an `option_mass` block, **32
readouts** disagree, **0 gate verdicts flip**. They have **not** changed it and asked whether I want it
fixed, since my analyses might quote the field.

**One number of mine reads it.** R-13/C-7 quotes `median = 0.03097` for
`semantic/semantic_one_word`, from `s3A_20260825_071225_2399639`, **n = 8** — even, so the off-by-one
applies. Per-row `option_mass` is not stored in `gens.jsonl`, so the exact true median is not
recoverable from the artifact.

**It does not need to be, because the direction is determined.** The upper-middle element is **≥** the
true median by construction, so:

* my quoted **0.0310 is an upper bound**; the true median is **≤ 0.0310 < 0.05** — R-13's
  `semantic_one_word` **BELOW GATE** verdict is unaffected and, if anything, understated;
* the two kinds I **selected** on that gate sit at **0.4687** and **0.3443**, roughly **7× and 6.9×**
  the 0.05 threshold. A bias whose corpus-wide median discrepancy is **0.0014** cannot have
  manufactured either pass.

#### The asymmetry, which is the part worth keeping

**A gate reading the upper-middle is biased toward passing.** So:

| historical verdict | can the bug have caused it? |
|---|---|
| **BELOW** | **No** — the true median is ≤ the reported one, so a BELOW verdict is safe *a fortiori* |
| **PASS** near the threshold | **Yes** — this is the only unsafe direction |

**Every BELOW in the corpus is trustworthy without re-checking; only near-threshold PASSes are
suspect.** That halves the audit surface, and it is why "0 verdicts flip today" is reassuring rather
than sufficient — the next readout that lands just under 0.05 is the one it bites.

**My recommendation on the fix, since they asked and it is shared code**: **do not mutate `median`.**
It appears in every historical `summary.json` and mutating it moves published values retroactively —
which is C-14's error in a different costume (correcting a figure by changing the thing that produced
it). Instead **add `median_true` alongside**, and **point the GATE at `median_true`**. Nothing already
published moves, and the gate stops being biased toward passing. **It is free to do now precisely
because 0 verdicts flip** — doing it after one flips would mean changing a verdict and a definition in
the same commit.

**⛔ Not my call alone and not my file** — `score_behavior.py` is shared and they own this change; this
is my answer to their question, recorded so the reasoning is inspectable rather than delivered only in
a message.


### ⛔ C-28 (02:35) — **C5 is narrowed to the bank it was measured on. The concurrent session's binding collapse is REAL, is on a DIFFERENT SCOPE than C5's headline, and their `main` number reproduces my `legacy` arm to four decimals.**

They report binding collapsing under *"the entry-6 retrieval knockout, `demo_all:attn_knockout:6-14`"*:
`main` **0.5416 → 0.3689** (mapped-wins 42/48 → 41/48) but `ticket_bomb` **0.5695 → 0.1162**
(**45/48 → 15/48**). They answered both of my qualifying questions correctly — it is **100%
`core2x2`**, `n=48`, and the family sets are **set-equal** across arms, so it is a within-family paired
contrast on a fixed 48, **C5's own shape**. No denominator problem.

**So I checked my own arms, and the first thing found was that we are not running the same
intervention.** Option mass on the forced-choice probe, Llama, the same
`boombness_prompt_bank.jsonl`:

| arm | scope | option mass |
|---|---|---|
| `p2A` (baseline) | — | **0.5416** |
| `p2_demo_processing_only` | **`demo_processing_only`** | **0.6021** |
| **`p2_legacy_all_query`** | **`legacy_all_query`** | **0.3689** |
| `p2_query_prefill_only` | `query_prefill_only` | 0.4365 |

**Their `main` baseline 0.5416 and knockout 0.3689 are my baseline and my `legacy_all_query` arm,
to four decimals.** The `--intervene` string is identical across all four of my arms —
`demo_all:attn_knockout:6-14:1.0` — and what differs is `--knockout-scope`. **So "the entry-6
retrieval knockout" is the UNSCOPED `legacy_all_query` mask**, which is exactly the *"one unscoped
mask"* §1 of this plan was written to decompose.

**What that does and does not do to C5.**

* **C5's headline arm is `demo_processing_only`, where mass RISES (0.5416 → 0.6021).** Their collapse
  is on a **sibling scope**, so it does **not** contradict C5's central number — and their own `main`
  result is consistent with my `legacy` arm rather than in tension with it. **This is a cross-session
  reproduction, not a disagreement.**
* **But C5 is measured on ONE BANK.** Both bridge runs — Llama `bridge_20260825_101613_3117657` and
  Qwen3 `qbridge_20260825_104155_3190213` — use `boombness_prompt_bank.jsonl`. C5's "Llama + Qwen3"
  is **two models on one bank**, not two banks.
* **They have now shown that binding-survival under a sibling scope is BANK-DEPENDENT** — surviving on
  `main`, collapsing five-fold on `ticket_bomb`. **That is a direct warning against assuming C5's
  bank-generality**, which nothing in my evidence establishes and which the claim's wording did not
  exclude.

**Correction applied**: C5 is stated as **`main` bank only**, with the sibling-scope bank-dependence
recorded beside it. **Not a retraction** — the within-family dissociation on `main` stands on both
models — **a scope narrowing**, the second C5 has taken (C-24 narrowed it to `core2x2` families).

**⛔ What is now open and is NOT being asserted either way**: whether `demo_processing_only`'s binding
survival holds on `ticket_bomb`. **Nobody has run it.** Their collapse is `legacy`; my survival is
`demoproc`; the cell that would decide C5's bank-generality is empty. **Recorded as unknown rather than
inferred from either neighbour.**


### 🔒 PR-32 (02:45, written and committed before the arms are submitted) — **fill the empty cell C-28 identified: does `demo_processing_only` preserve binding on `ticket_bomb`, where the unscoped mask collapses it five-fold?**

**Why this is not the invented work R-76 forbade.** The gap was **created by evidence that arrived
tonight**, not derived from a limitation I went looking for: the concurrent session showed binding
collapsing on `ticket_bomb` under `legacy_all_query` (**0.5695 → 0.1162**, mapped-wins **45/48 →
15/48**) while C5's `demo_processing_only` arm on `main` shows mass **rising** (0.5416 → 0.6021).
**C-28 recorded the deciding cell as empty; this fills it.**

**It is also cheap and needs no new bank.** `boombness_prompt_bank_ticket_bomb.jsonl` already carries
**288** forced-choice rows, all `core2x2`; filtered to `natural_doublespeak` × `n_examples ∈ {1,2,4,8}`
it is **48 rows — the same population the peer used.** Forward-only probes: `--max-new 8`, no
generation to judge, no GPU-hours beyond two short loads.

**Design.** Exactly the `p2_*` configuration with the bank swapped — Llama-3.1-8B, band **6-14**,
`--query-kinds semantic_forced_choice --conditions natural_doublespeak --bank-blocks
core2x2,core2x2_slot3 --n-examples 1,2,4,8 --expect-n 48 --max-new 8 --min-option-mass 0.05
--attn-impl eager`. **Two arms, both mine end to end** so the pair is same-bank and same-session:
`tbA` (baseline) and `tb_demoproc` (`--intervene demo_all:attn_knockout:6-14:1.0 --knockout-scope
demo_processing_only`). **Nothing is retuned.**

#### 📌 Gate first

**The baseline must show binding to preserve**: `mapped_wins` clearly above chance **and** median
option mass **≥ 0.05** (the same floor R-13 used to select this probe). If the baseline does not bind
on this bank, there is nothing for the intervention to preserve or destroy and this **DECLINES** —
R-52's rule. *(The peer's `ticket_bomb` baseline was 45/48 at mass 0.5695, so I expect this to pass;
expecting it does not excuse skipping it.)*

#### 📌 Conditions, fixed now

Let `d_demoproc = mapped_wins(demoproc) − mapped_wins(baseline)`, and the peer's measured
`d_legacy = 15 − 45 = −30` on this same population.

1. **BINDING SURVIVES** if `demoproc` stays within the noise of baseline — `|d_demoproc| ≤ 3 rows` of
   48 — **and** its median option mass stays **≥ 0.05**.
2. **BINDING COLLAPSES** if `d_demoproc ≤ −15` rows, i.e. at least half the way to `legacy`'s −30.
3. **INTERMEDIATE** otherwise, and is reported as intermediate rather than forced into either bucket.

**Reported alongside, per PR-28's declared statistic** (the readout is deterministic — forced choice,
no judge): the **paired exact test on discordant families**, plus the mass, plus the row counts.

#### ⛔ What each outcome means, written before the data exists

* **SURVIVES** → the scope decomposition is what carries binding survival: the unscoped mask destroys
  binding on this bank and the scoped one does not. **That is a STRONGER result than C5 currently
  claims** and it would restore bank-generality to C5's *scoped* form while leaving the unscoped form
  bank-dependent.
* **COLLAPSES** → **C5 narrows again, hard**: binding survival is a property of the `main` bank, not of
  the intervention, and "concept binding survives" cannot be stated without naming the bank. C-28's
  narrowing would become the headline rather than a caveat.
* **INTERMEDIATE** → C5 is stated as bank-sensitive with a measured gradient, and neither of the clean
  stories is told.

**⛔ Pre-committed as NOT counting**: any behavioural/ASR number on this bank (none is being generated),
and any comparison to the peer's `legacy` arm other than as the **reference collapse** it already is —
their run is theirs, and I am not re-deriving their number, only my own two arms.


### 🏆 R-93 (03:10) — **PR-32: BINDING SURVIVES on `ticket_bomb` under `demo_processing_only` — 45/48 → 45/48, where the unscoped mask gives 45/48 → 15/48 on the same 48 rows. The SCOPE is what destroys binding, not the bank.**

Artifacts `tbA_20260828_024412_1186606` and `tb_demoproc_20260828_024522_1186992`: 48/48 rows each,
`failures: 0`, `frac_rows_scope_live = 1.0`, `scope_violations = {}`, family sets **set-equal**, so it
is a paired within-family contrast on a fixed 48 — C5's own shape.

**Gate passed**: baseline binds at **45/48** with median option mass **0.5695** — which **reproduces
the concurrent session's `ticket_bomb` baseline to four decimals**, a second cross-session
reproduction after C-28's.

**The three pre-registered conditions:**

| | | |
|---|---|---|
| mapped-wins | **45/48 → 45/48**, `d = +0` | |
| median option mass | **0.5695 → 0.5305** (≥ 0.05) | |
| discordant / paired exact | 2/2, **p = 1.0** | |
| **1 SURVIVES** — \|d\| ≤ 3 and mass ≥ 0.05 | **TRUE** | ✅ |
| 2 COLLAPSES — d ≤ −15 | false | |
| 3 INTERMEDIATE | false | |

**Side by side on the identical 48 rows and the identical `--intervene` string:**

| scope | mapped-wins | option mass |
|---|---|---|
| baseline | 45/48 | 0.5695 |
| **`demo_processing_only`** | **45/48** *(d = 0)* | **0.5305** |
| `legacy_all_query` *(peer)* | **15/48** *(d = −30)* | **0.1162** |

**The only difference between those two arms is `--knockout-scope`.** Same bank, same model, same
band 6-14, same mask specification. **The unscoped mask destroys binding on this bank; the scoped one
leaves it untouched.**

#### What this does to C5 — the outcome PR-32 pre-committed as the stronger one

C-28 narrowed C5 to the `main` bank three ticks ago because the peer's collapse suggested
bank-dependence. **That inference is now wrong in the direction that matters**: the collapse was
**scope**-dependence wearing bank-dependence's clothes. On the bank where binding was supposed to be
fragile, **C5's own scope preserves it perfectly.**

**So C5's scoped form recovers its generality**: `demo_processing_only` preserves binding on **two
banks** (`main` 0.5416 → 0.6021 rising; `ticket_bomb` 45/48 → 45/48) and **two models** on `main`.
**C-28's bank restriction is lifted for the scoped claim and retained for the unscoped one**, which is
where the evidence actually puts it.

**⚠ What is NOT claimed.** `ticket_bomb` adds a **second bank on Llama only** — Qwen3 remains
single-bank, so C5 is not "two models × two banks". The mass does drop (0.5695 → 0.5305, ~7%) where on
`main` it rose; that is **within the survival criterion and is not nothing**, and I am recording the
direction rather than rounding it to "unchanged". And the `+0` is a **net** of 2 discordant each way,
not 48 identical decisions.

**The finding beneath the finding.** C-28 was a correct, evidence-driven narrowing that turned out to
be **attributing an effect to the wrong variable** — bank instead of scope — because the two were
confounded in the only comparison available at the time. **The fix was not more caution; it was the
one run that separated them.**


### ✅ R-94 (03:15) — **The deciding cell was run INDEPENDENTLY by both sessions and the results agree to the last digit — once the same median estimator is used. The residual gap was R-92's off-by-one, and this measures it on live data.**

Their V-35 ran the same cell I ran in PR-32, on the same bank and population, without either of us
seeing the other's numbers first. **Mapped-wins agree exactly:**

| arm | mine (R-93) | theirs (V-35) |
|---|---|---|
| baseline | **45/48** | **45/48** |
| `demo_processing_only` | **45/48** | **45/48** |
| `legacy_all_query` | — | **15/48** |

**The option masses did not agree, and the discrepancy is diagnostic rather than troubling.** Mine
read **0.5695 / 0.5305**; theirs read **0.5534 / 0.5201**. Their own `ticket_bomb` baseline had also
moved between messages — **0.5695 → 0.5534** — which is the signature of an estimator change, not a
re-run. Computed directly from my own `results.jsonl`:

| arm | `summary.json` `median` field | upper-middle `v[n//2]` | **true median** | their V-35 |
|---|---|---|---|---|
| `tbA` | 0.5695 | 0.5695 | **0.5534** | **0.5534** ✅ |
| `tb_demoproc` | 0.5305 | 0.5305 | **0.5201** | **0.5201** ✅ |

**Their numbers are the true medians of my rows.** They landed the `median_true` fix in V-34 —
the change R-92 recommended — so their reader now reports the true median while my `summary.json`
still carries the upper-middle in the legacy `median` field, exactly as designed so nothing published
moves.

**Two things this settles.**

1. **The independent replication is exact.** Two sessions, two runs, same bank, same population, and
   after normalising the estimator **every number matches**: 45/48, 45/48, 0.5534, 0.5201. R-93's
   conclusion — *the scope destroys binding, not the bank* — is now a **two-session result**.
2. **R-92's off-by-one is measured on live data rather than argued.** The bias is **+0.0161** and
   **+0.0104** here (upper-middle above true median), consistent in direction with the construction
   argument and with their corpus-wide median discrepancy of 0.0014. **My quoted masses are upper
   bounds**, which is the direction that mattered for R-13's BELOW verdict and matters not at all for
   a survival criterion of ≥ 0.05.

**⚠ One thing to keep straight in any write-up**: my log quotes `0.5695 / 0.5305` and theirs quotes
`0.5534 / 0.5201` **for the same runs**. Neither is wrong — they are different estimators of the same
quantity — but **quoting both without saying which is which would look like a contradiction.** R-93's
numbers are hereby annotated as upper-middle; the true medians are recorded above.

**Their `comprehension_usage` result, which I did not run**, points the same way and further:
baseline 11/48, `legacy` 3/48, **`demoproc` 17/48** — the scoped knockout *raises* the coded reading.
**Recorded as theirs, not adopted**, since I have no arm of my own on it.


### 🏆 R-95 (03:45) — **The behavioural half of the deciding cell lands, and it turns R-93 from a probe reading into a MECHANISM DISSOCIATION: the two scopes remove the same attack by different routes. My refusal decomposition corroborates theirs on a third bank.**

The concurrent session ran the behavioural arms on `ticket_bomb` that PR-32 deliberately did not
(PR-32 pre-committed *"any behavioural/ASR number on this bank"* as not counting, because I generated
none). Same population, cap 640, n=96, **all three arms in one judge invocation**:

| arm | ASR | Δ | down/up | refusal | median len |
|---|---|---|---|---|---|
| baseline | 30/96 | — | — | 12/96 | 248.0 |
| `legacy_all_query` | **2/96** | **−0.2917** | 29 ↓ / 1 ↑ | **0/96** | 299.5 |
| `demo_processing_only` | **8/96** | **−0.2292** | 26 ↓ / 4 ↑ | **22/96** | 282.0 |

**Set beside R-93's probe numbers on the identical population**, the picture is not two magnitudes of
one effect:

| | binding (mapped-wins) | ASR removed | refusal |
|---|---|---|---|
| `legacy_all_query` | **15/48 — destroyed** | 29 | **falls to 0** |
| `demo_processing_only` | **45/48 — intact** | 26 | **rises 12 → 22** |

**The unscoped mask removes the attack by removing access to the mapping. The scoped mask removes it
while the mapping stays available and reportable.** That is a **mechanism dissociation**, and it is
their framing, which I think is right and better than "the scoped arm is slightly weaker".

#### The complication they flagged, checked against my own data rather than accepted

They noted that `demoproc`'s effect **is not purely non-refusal**: 8 of 26 down-flips are refusals
(31%), and its keyword refusal rate **rises** where `legacy`'s falls to zero. **Recomputed my own
decomposition from the judge artifacts** rather than quoting C-9b's log line:

| population | down-flips | refused | non-refusal |
|---|---|---|---|
| Llama `d10` (`p1k`) | 15 | **3 (20%)** | 12 |
| Qwen3 (`q1j`) | 17 | **4 (24%)** | 13 |
| **their `ticket_bomb`** | 26 | **8 (31%)** | 18 |

**Three banks, two models, and the refusal share is 20% / 24% / 31% — a minority everywhere and
never zero.** C-9b's *"not mostly refusal"* is corroborated on a bank I never ran; their 31% is the
high end of a consistent range rather than a contradiction.

**But their caveat is the honest one and I am adopting it**: *"if C5's story is 'the mapping survives
and the model declines to use it', the refusal component is part of how it declines."* **C2 says
refusal restoration is not the ROUTE to attack removal, and that survives — 69-80% of down-flips are
non-refusal across all three banks. It does not license calling refusal absent**, and the contrast
with `legacy`'s **0/96** is what makes refusal informative rather than incidental: the scope that
preserves binding is also the scope that refuses.

**⚠ Recorded as theirs, not adopted as mine.** I generated no behavioural arm on `ticket_bomb` and
PR-32 pre-committed not to claim one. Their caveats travel with it: **one bank for the scoped
comparison, one model, n = 96, and `main`'s scoped ASR arm unrun.** Their gate note also travels —
**all of it is the retrieval knockout, not a boombness objective**, so none of it speaks for Phase 7.

**Their entry 6 closes consistently with R-84**: `main` −0.1458 (p=0.0125), `ticket_bomb` −0.2604
(p≈0), `basket_gun` **−0.0312, p=0.5488, null** — reported **per population** rather than pooled,
with MDE 0.094 exceeded by both confirmers and **divergence 96/96 on the null**, so the hook fired and
changed every generation while ASR did not move. **Live and inert — a dissociation, not a dead arm**,
which is exactly the distinction the invariant exists to draw.


### ⚠ R-96 (03:50) — **R-95's mechanism story is HALF right, and my own arms show which half. `demo_processing_only` behaves identically on both banks; `legacy_all_query` does NOT — on `main` it removes the attack while leaving binding intact, so "the unscoped mask works by removing access to the mapping" is bank-specific.**

Their caveat list said *"`main`'s scoped ASR arm hasn't been run."* **It has — by me, at cap 192**
(`p1k_*` behavioural and `p2_*` probe, both on `boombness_prompt_bank.jsonl`). So the 2×2 of
**bank × scope**, on **both** readouts, is already complete across the two sessions. Assembled:

| bank | arm | ASR | refusal | binding (mapped-wins) |
|---|---|---|---|---|
| **main** | baseline | **16/96 †** | 3/96 | 42/48 |
| main | `legacy_all_query` | **3/96 †** | **1/96** ↓ | **41/48 — INTACT** |
| main | `demo_processing_only` | **4/96 †** | **20/96** ↑ | **48/48 — raised** |
| **ticket_bomb** | baseline | 30/96 | 12/96 | 45/48 |
| ticket_bomb | `legacy_all_query` | **2/96** | **0/96** ↓ | **15/48 — DESTROYED** |
| ticket_bomb | `demo_processing_only` | **8/96** | **22/96** ↑ | **45/48 — intact** |

**† = ASR within the first 192 generated tokens** (over half of every `main` row is at the cap); the `ticket_bomb` ASR figures are plain ASR at cap 640. **The two ASR columns are NOT comparable — C-29.** The binding and refusal columns are cap-free and are.

#### What replicates and what does not

**`demo_processing_only` is consistent on both banks**: removes most of the attack (16→4, 30→8),
**raises** refusal (3→20, 12→22), and **preserves or raises** binding (42→48, 45→45). **That is C5 and
C2 holding together on two banks, and it is the half R-95 got right.**

**`legacy_all_query` is NOT consistent.** On `ticket_bomb` it destroys binding (**45→15**); on `main`
it leaves binding **intact at 41/48** while still removing the attack (16→3). **So R-95's sentence —
*"the unscoped mask removes the attack by removing access to the mapping"* — is true on `ticket_bomb`
and FALSE on `main`.** On `main` the mapping stays available, refusal *falls*, and the attack goes
anyway. **That is a third route, not the one I recorded an hour ago.**

**I adopted their framing and it was over-general.** The dissociation I should have stated is the one
that actually replicates: **the two scopes differ in their REFUSAL signature on both banks** — `legacy`
refuses *less* (3→1, 12→0), `demoproc` refuses *more* (3→20, 12→22) — **while their effect on binding
is bank-dependent for `legacy` and bank-stable for `demoproc`.**

**This is not a correction to any number** — theirs and mine both recompute — **it is a correction to a
mechanism sentence I imported without testing it on the bank I already had.** R-95 recorded their
result faithfully and then generalised its interpretation one bank too far; the arms that refute the
generalisation were sitting in my own outputs while I wrote it.

**What it does to C5**: unchanged and slightly strengthened — `demo_processing_only` preserves binding
on **both** banks (42→48, 45→45), which is what R-93 claimed. **What it does to the phase's story**:
the clean *"scoped preserves, unscoped destroys"* headline **is not available**; the unscoped mask only
destroys binding on one of two banks, and why it does there and not here is **unexplained and not
being explained by me tonight.**


### ⛔ C-29 (03:55) — **R-96's table put an ASR-within-192 column next to a plain-ASR column without labelling either. Caught by the concurrent session. The conclusion survives because it never rested on that column — but the table as written invites the comparison my own DR-2 rule forbids.**

R-96 assembled a bank × scope table to test R-95's mechanism sentence. They flagged that **`main`'s
rows are cap 192 and `ticket_bomb`'s are cap 640**, so the ASR column mixes two different quantities.
**Verified on my own artifacts:**

| arm | `max_new` | frac at cap |
|---|---|---|
| `p1A` (main baseline) | **192** | **0.562** |
| `p1_legacy_all_query` | **192** | 0.552 |
| `p1_demo_processing_only` | **192** | **0.719** |
| ticket_bomb behavioural (theirs) | **640** | 0.000 |

**More than half of every `main` row is at the cap.** So `16/96` and `3/96` are **ASR-within-192**;
`30/96` and `2/96` are **plain ASR**. DR-2 fixed the rule that every ASR travels with its cap, and my
own R-92/R-94 work turned on exactly this kind of estimator mismatch — **I then built a table that
juxtaposes the two without a label.**

**Corrected in place**: the ASR column now reads **`16/96 †` / `3/96 †` / `4/96 †`** for `main` with
**† = ASR within the first 192 generated tokens**, and the `ticket_bomb` rows unmarked as plain ASR at
cap 640.

#### Why R-96's conclusion is unaffected — checked, not assumed

R-96 concluded two things, and **neither uses the ASR column**:

1. **`legacy` destroys binding on `ticket_bomb` and not on `main`** — from the **forced-choice probe**,
   which runs `--max-new 8` **forward-only with no generation**. `p2A` and `tbA` both carry
   `max_new=8`. **No cap is involved on either side; the comparison is clean.**
2. **The refusal signature separates the scopes on both banks** — and **R-75 measured refusal to be
   cap-invariant row-for-row** (81/96 completions changed between caps, **0** refusal decisions moved).
   **Cap-mixing cannot reach it.**

**So the finding stands and the presentation was wrong.** That distinction matters: the fix is a label,
not a retraction — but an unlabelled table is how a reader ends up making the comparison the author
avoided.

**The pattern, for the fourth time in this exchange**: an artifact that is individually correct in each
cell and misleading in how the cells are set beside each other. C-20 (a live hook that changed
nothing), C-26/C-27 (passing tests that checked nothing), R-94 (two correct medians of the same rows),
and now this. **Every one was caught by someone comparing against something that should have
differed** — and this one by the session whose numbers I was tabulating.


### ⛔ R-97 (04:10) — **The deciding cell DOES NOT DECIDE: `basket_gun`'s baseline does not bind (19/48, BELOW chance), so it cannot arbitrate whether `legacy` destroying binding is the norm. R-96's question stays open.**

Their three `basket_gun` probe arms completed (`p5A_gun`, `p5L_gun`, `p5D_gun`), which is the cell I
suggested for turning R-96's 1-of-2 binding split into a 2-of-3. **Read from their artifacts, the
comparable readout is `semantic_forced_choice`, n = 48:**

| bank | baseline mapped-wins | rate |
|---|---|---|
| `main` | 42/48 | **0.875** |
| `ticket_bomb` | 45/48 | **0.938** |
| **`basket_gun`** | **19/48** | **0.396 — BELOW the 0.500 chance line** |

**The model does not bind the concept on this bank.** *(⛔ C-31: originally written as "prefers the codeword" — wrong. 19/48 is **p = 0.193** against chance, so the mapping is ABSENT, not inverted.)* There is no
binding to destroy or preserve, so the arms cannot answer the question:

| arm | mapped-wins | mass |
|---|---|---|
| baseline | 19/48 | 0.3869 |
| `legacy_all_query` | **11/48** | 0.3617 |
| `demo_processing_only` | **23/48** | 0.3872 |

**`legacy` at 11/48 must NOT be read as "binding destroyed on a third bank."** It is a drop from a
baseline that was already below chance — precisely the shape of their own `window_knife` (baseline
ASR 2/96, *"evidence of nothing"*), of R-52's underpower decline, and of the gate PR-32 imposed on
itself: **the baseline must bind before "does the intervention preserve binding" is a question.**
**`basket_gun` FAILS that gate.**

**So R-96's open question is untouched**: `legacy` destroys binding on `ticket_bomb` and leaves it
intact on `main`, and **a third informative bank has not been found.** Two of three, not two of three.

*(The directions are still consistent with everything else — `demoproc` moves mapped-wins **up**
19 → 23 while `legacy` moves it **down** 19 → 11 — but from a non-binding baseline that is
uninterpretable and I am not counting it.)*

#### ⚠ A near-miss of my own, recorded because it nearly became the finding

**My first read of this was `55/144` pooled across THREE query kinds** — `semantic_forced_choice`,
`semantic_one_word` and `comprehension_usage` all carry `p_concept`, and my filter took every row with
that field. I was about to report a below-chance baseline from a number that **mixed three different
readouts with different scales** — `forced_choice` mass 0.3869 against `one_word` mass 0.0808, which
R-13 measured as below its own reportability floor.

**The conclusion happens to survive** — `forced_choice` alone is 19/48 = 0.396, still below chance —
**but it survived by luck, not by method.** Splitting by `query_kind` was the check, and I ran it
because their filter line said three kinds while my mental model said one. **The same class as C-29
one tick earlier: cells that are individually fine, pooled across a dimension that makes them
incomparable.**


### ✅ R-98 (04:20) — **Their "the mapping never installs on `basket_gun`" account is not just coherent — it is directly measurable, and the dose-response confirms it. On two banks binding saturates at 1.000; on `basket_gun` it never reaches chance at any dose.**

**⚠ Read with R-100:** every bank compared here varies **codeword AND concept together**, so the cross-population ordering below cannot be decomposed into codeword, concept, or demonstration sentences. The concurrent session is now running the disconfounding 2×2 (`ticket_knife`, `window_bomb`, `window_knife` at cap 640).

They proposed that `basket_gun`'s weakness on every axis (baseline ASR 10/96, forced-choice 0.396,
knockout effect −0.031 null) is one account rather than three: **the doublespeak mapping does not
install on that bank**, so there is nothing for a knockout to remove. **That is an inference from
endpoints. It is testable directly** — if the mapping installs, binding should GROW as demonstrations
accumulate; if it never installs, the dose ladder is flat.

**Baseline forced-choice mapped-wins by dose, 12 rows per cell:**

| bank | n=1 | n=2 | n=4 | n=8 | Δ(8−1) |
|---|---|---|---|---|---|
| `main` | 8/12 = 0.667 | 11/12 = 0.917 | 11/12 = 0.917 | **12/12 = 1.000** | **+0.333** |
| `ticket_bomb` | 9/12 = 0.750 | **12/12 = 1.000** | 12/12 = 1.000 | 12/12 = 1.000 | +0.250 |
| **`basket_gun`** | 4/12 = 0.333 | 5/12 = 0.417 | 5/12 = 0.417 | 5/12 = **0.417** | **+0.083** |

**⛔ R-102 NARROWS THIS: `basket_bomb` installs on the same codeword, so the failure is the CONCEPT `gun`, not the bank — read "does not install for the `gun` concept".** **On `main` and `ticket_bomb` the mapping installs and saturates** — both reach **12/12** and stay
there. **On `basket_gun` it never crosses chance at any dose**, and the apparent rise is **one row in
twelve**, flat within noise.

**So their account is confirmed by a measurement rather than supported by a pattern.** `basket_gun`'s
null is **not** "the knockout fails here" — it is **"there is no installed mapping to knock out"**, and
the dose ladder shows the failure is at installation rather than at any later stage.

**This improves two readings that were both weaker than they needed to be:**

* **Their entry-6 null** on `basket_gun` (−0.031, p=0.5488) was reported as a population-specific
  null with the hook demonstrably live (divergence 96/96). **It is better read as a population where
  the phenomenon was never present** — which their own `window_knife` (baseline ASR 2/96) likely is too. **⛔ REFUTED by PR-33/R-99: `window_knife` installs the mapping completely (0.583 → 1.000, mass 0.7681). Low ASR does NOT imply non-installation, and this hedge was wrong.**
* **R-97's decline** — I ruled `basket_gun` uninformative because its baseline sits below chance.
  **That is right and now has a mechanism**: below chance because the mapping never installed, not
  because the probe failed.

**⚠ Cell sizes are 12.** Every number above is out of twelve rows, so the *shape* (flat vs saturating)
is the claim and no individual cell is. The two saturating banks reach a ceiling, which is the least
noise-sensitive thing a dose ladder can do; **`basket_gun`'s flatness rests on 4/12 → 5/12 and would
not survive being quoted as a rate.**

**⚠ And this is a BASELINE property, not an intervention result.** Nothing here involves a knockout.
It says what the bank does before anything is done to it — which is exactly why it explains the null
instead of being another instance of it.


### 🔒 PR-33 (04:20, written and committed before the arm is submitted) — **convert R-98's hedge into a measurement: does `window_knife` also fail to install the mapping?**

R-98 wrote that the concurrent session's `window_knife` population (**baseline ASR 2/96**) *"likely
is too"* a non-installation case. **That is a hedge in a document whose whole discipline is not
hedging where a measurement is available**, and the measurement costs one forward-only probe arm.

**It is falsifiable, which is the point.** If `window_knife`'s baseline **binds**, then low baseline
ASR does **not** imply non-installation, R-98's "likely" was wrong, and their entry-6 null on that
population needs a different explanation. **I am running my own prediction against the possibility
that it fails.**

**Design.** One arm, baseline only, no intervention. `boombness_prompt_bank_window_knife.jsonl`
(codeword `window`, concept `knife`) — **48 rows**, `natural_doublespeak` ×
`semantic_forced_choice` × `n_examples ∈ {1,2,4,8}`, **12 per dose**, identical to `p2A`/`tbA`/`p5A_gun`.
Llama-3.1-8B, `--max-new 8`, forward-only, `--min-option-mass 0.05`, `--attn-impl eager`. **Nothing is
retuned and no intervention arm is run** — the claim is about the *baseline*.

#### 📌 Conditions, fixed now against the three banks already measured

Reference dose ladders (mapped-wins, 12/cell): `main` 0.667→**1.000**; `ticket_bomb` 0.750→**1.000**;
`basket_gun` 0.333→0.417, **never crossing 0.500**.

1. **NON-INSTALLATION (R-98's prediction holds)** — baseline mapped-wins **never reaches 0.500 at any
   dose**, and `Δ(n=8 − n=1) ≤ +0.15`. `window_knife` joins `basket_gun`, and **two of five entry-6
   populations are positively identified as non-installation rather than inferred.**
2. **INSTALLATION (prediction REFUTED)** — mapped-wins **crosses 0.500 and rises**, i.e. it looks like
   `main`/`ticket_bomb`. Then **low baseline ASR does NOT imply non-installation**, R-98's hedge was
   wrong to lean that way, and their `window_knife` null needs a different account. **I would record
   that as a refuted prediction of mine, not as a peer's problem.**
3. **AMBIGUOUS** — crosses chance but flat, or rises without crossing. Reported as ambiguous; **no
   story is fitted to it.**

**⛔ Pre-committed as NOT counting**: the option-mass number on its own (`basket_gun` sat at 0.3869
mass while failing to bind, so mass and binding are separable and mass alone decides nothing here),
and any ASR statement — **I am generating no completions.**

**⚠ And the standing caveat from R-98 applies unchanged**: cells are **12 rows**, so the *shape* is the
claim and no individual cell is.


### ⛔ R-99 (04:40) — **PR-33 REFUTES MY OWN PREDICTION. `window_knife` installs the mapping perfectly (0.583 → 1.000, saturating) despite a baseline ASR of 2/96. So low ASR does NOT imply non-installation, and R-98's hedge leaned the wrong way.**

**⚠ Read with R-100:** every bank compared here varies **codeword AND concept together**, so the cross-population ordering below cannot be decomposed into codeword, concept, or demonstration sentences. The concurrent session is now running the disconfounding 2×2 (`ticket_knife`, `window_bomb`, `window_knife` at cap 640).

PR-33 was written to convert R-98's *"`window_knife` likely is too"* into a measurement, explicitly
*"running my own prediction against the possibility that it fails."* **It failed.**

| bank | n=1 | n=2 | n=4 | n=8 | Δ | verdict |
|---|---|---|---|---|---|---|
| `main` | 0.667 | 0.917 | 0.917 | **1.000** | +0.333 | installs |
| `ticket_bomb` | 0.750 | **1.000** | 1.000 | 1.000 | +0.250 | installs |
| **`window_knife`** | **0.583** | 0.833 | 0.833 | **12/12 = 1.000** | **+0.417** | **INSTALLS** |
| `basket_gun` | 0.333 | 0.417 | 0.417 | 0.417 | +0.083 | never installs |

Overall **39/48 = 0.812**, true-median option mass **0.7681** — the *highest* mass of any bank
measured, against `basket_gun`'s 0.3869. **Condition 2 (INSTALLATION) fires; condition 1
(NON-INSTALLATION) is false.**

#### What this refutes, stated as a correction to my own reasoning

**R-98 wrote that `window_knife` "likely" shares `basket_gun`'s non-installation, on the strength of
its baseline ASR being 2/96.** That inference is **wrong**: `window_knife` has the strongest binding
of the four banks and an ASR near zero. **Low ASR and non-installation are independent** — a bank can
install the mapping completely and still not produce successful attacks.

**So the tidy story R-98 offered the concurrent session — "two of five entry-6 populations are
non-installation rather than non-effect" — collapses to one.** `basket_gun` remains a genuine
non-installation case (measured, R-98). **`window_knife` is not, and its entry-6 null needs a
different explanation than the one I proposed.** I have told them; the hedge was mine and so is the
retraction.

**What survives untouched**: R-98's `basket_gun` finding, which was measured rather than inferred —
flat ladder, never crossing chance. **The method was right and the extrapolation from it was not.**
That is the distinction PR-33 existed to draw, and it drew it against me.

#### Why this was worth one probe arm

R-98's hedge was doing real work in the argument — it turned a single measured population into a
pattern, and a pattern into a recommendation for how the peer should read their limitation section.
**Twenty minutes of forward-only compute showed the pattern did not exist.** Had I left the word
"likely" in place, it would have travelled into their write-up as support for a generalisation that
the very next bank contradicts.

**⚠ Open, and explicitly not answered here**: what *does* explain `window_knife`'s ASR of 2/96 given
that its mapping installs completely. **Binding is necessary and evidently not sufficient for the
attack**, which is a restatement of this phase's central dissociation (C5/C2) on a fourth bank — but I
have run **no** behavioural arm here and am not inferring one from a probe.


### ⚠ R-100 (04:45) — **Every population compared across this sprint varies CODEWORD and CONCEPT together. That confound is a design fact, not an inference — and it offers a free explanation for R-99's open question that no one has tested.**

R-99 left open why `window_knife` shows ASR **2/96** while installing the mapping perfectly. **Reading
the bank metadata rather than theorising**, the four measured populations line up like this:

| bank | codeword | concept | baseline ASR | binding at n=8 |
|---|---|---|---|---|
| `main` | `carrot` | **bomb** | **22/96** | 1.000 |
| `ticket_bomb` | `ticket` | **bomb** | **30/96** | 1.000 |
| `basket_gun` | `basket` | **gun** | **10/96** | 0.417 |
| `window_knife` | `window` | **knife** | **2/96** | 1.000 |

**ASR orders exactly by concept — bomb (22, 30) > gun (10) > knife (2) — and binding does not order by
anything.** Three banks install completely and one does not, cutting across the ASR ordering.

#### The confound is certain even though the explanation is not

**Every one of these populations changes the codeword AND the concept at the same time.** So a
"population-specific effect" — which is how the concurrent session's entry 6 is currently framed, and
how R-98 and R-99 both discussed it — **cannot be decomposed into codeword, concept, or demonstration
sentences.** That is not a hypothesis about the data; it is a property of which banks exist.

**The concept explanation for `window_knife` is a hypothesis and I am labelling it one**: StrongREJECT
may simply score knife-related compliance lower than bomb-related compliance, in which case
`window_knife`'s 2/96 is a **property of the harm category, not of the mechanism**, and there is
nothing to explain. **Four points with one or two per concept cannot establish that** — the ordering
is suggestive and the sample is a design artifact.

#### The controlled pairs already exist

The bank directory contains **same-codeword, different-concept** pairs that separate the two axes at
zero build cost:

* `ticket_bomb` ↔ **`ticket_knife`**
* `window_bomb` ↔ **`window_knife`**
* `basket_bomb` ↔ `basket_gun` ↔ `basket_knife` ↔ `basket_club`
* `button_bomb` ↔ `button_gun` ↔ `button_knife` ↔ `button_club`

**`ticket_bomb` is already measured at 30/96.** A behavioural arm on `ticket_knife` — codeword held
fixed, concept swapped — would say directly whether the ASR spread is concept-driven. **If it lands
near 2/96, concept explains it and several "population-specific" readings across this sprint are
harm-category readings.** If it lands near 30/96, the concept hypothesis dies and the spread is about
the demonstration sentences.

**⛔ I am not running it.** It needs generation plus judging on a population that belongs to the
concurrent session's entry 6, and it would answer *their* limitation section rather than any open
question of mine — R-76's standard. **What I am contributing is the observation that the comparison
they and I have both been making is confounded by construction, and that the disconfounding banks are
already on disk.** Passed to them.

**⚠ This does not touch any claim of mine.** C1, C2, C5 and C7 are all *within*-bank contrasts —
baseline versus intervention on the same population — so a between-bank confound cannot reach them.
**It bears on the cross-population talk this sprint has been doing for the last several ticks**,
including mine in R-98 and R-99.


### 🏆 R-101 (05:45) — **The 2×2 lands and R-100's hypothesis is CONFIRMED: the ASR spread is CONCEPT, not codeword. Concept effect +0.240 against a codeword effect of +0.031 — roughly 8×. `window_knife`'s "dissociation" is largely a harm-category effect.**

They ran the disconfounding design I flagged, and went past my single-arm suggestion to a full
`{ticket, window} × {bomb, knife}` at cap 640. **Recomputed from their `results.jsonl` rather than
taken from a message:**

| | **bomb** | **knife** |
|---|---|---|
| **ticket** | **0.312** (30/96) | **0.052** (5/96) |
| **window** | **0.260** (25/96) | **0.042** (4/96) |

| effect | size |
|---|---|
| **concept** (bomb − knife) | **+0.240** |
| codeword (ticket − window) | **+0.031** |

**The concept main effect is roughly an order of magnitude larger than the codeword effect** *(⛔ C-30: the exact ratio is NOT quotable — this table mixed judge invocations and the ratio moves from 8× to 14.3× on one cell's re-judge; the direction and magnitude-class survive, the two-significant-figure ratio does not)*, and the two knife cells agree
with each other (0.052, 0.042) as do the two bomb cells (0.312, 0.260). **R-100's hypothesis —
labelled a hypothesis when I wrote it — is now measured.**

#### What this does to the result the concurrent session was about to build on

R-99 found `window_knife` installs the mapping completely (0.583 → **1.000**, mass 0.7681) while its
attack essentially never lands. They called that the cleanest instance of *"binding necessary, not
sufficient"* in the sprint — **a baseline property, no intervention, no liveness question** — and said
they would lead a paper section with it over V-36.

**That reading is now substantially weakened, and by the measurement I asked for.** `window_knife`'s
ASR is **0.042**, and *every* knife bank sits at **~0.05 regardless of codeword**. So the gap between
"mapping installed" and "attack lands" on that bank is **largely explained by the harm category being
scored low**, not by the mapping failing to drive behaviour. **A bank whose concept StrongREJECT rarely
scores above threshold will show binding-without-attack whatever the mechanism does.**

**What survives, stated precisely so it is not over-corrected either**: binding at **1.000** with ASR
at **0.042** is still binding without attack, and the concept effect does not make that arithmetic
false. **What it removes is the inference that the gap reveals something about the mapping's causal
role** — the same gap appears on `ticket_knife` (0.052), and nobody has claimed a mechanism there.
**The dissociation is real and its explanation is now mostly mundane.**

#### The methodological point, which is the one I would keep

R-100 was **free** — no GPU, no new runs, just reading four `_meta.json` files and noticing that every
compared population varied two things at once. **It overturned a headline that two sessions had
converged on and that one was about to write up.** The expensive part of this exchange has consistently
been the runs; **the corrections have kept coming from cheap structural checks nobody had run because
the numbers looked fine.**

**⚠ Not yet known and not assumed**: whether `ticket_knife` and `window_bomb` *install* the mapping.
Only `window_knife`'s ladder is measured (mine, R-99). **If the knife banks install and still score
0.05, the harm-category account is complete; if they do not install, there are two effects tangled
here and I would not separate them from the ASR column alone.**


### 🔒 PR-34 (05:45, written and committed before the arms are submitted) — **apply R-100's confound to MY OWN R-98: is `basket_gun`'s non-installation the codeword or the concept?**

R-100 caught that every compared population varies codeword and concept together, and R-101 confirmed
it on ASR. **I flagged that it "bears on my R-98" and then did not test R-98.** Doing that now.

**The installation data has exactly the same defect:**

| bank | codeword | concept | installs? |
|---|---|---|---|
| `main` | carrot | bomb | YES |
| `ticket_bomb` | ticket | bomb | YES |
| `window_knife` | window | knife | YES |
| **`basket_gun`** | **basket** | **gun** | **NO** |

**`basket_gun` is the only non-installer, the only `basket` bank, and the only `gun` bank.** R-98
concluded *"the mapping does not install on `basket_gun`"* and the concurrent session built its
entry-6 null reading on that. **Neither of us can say which factor is responsible**, and the sentence
as written implies the bank as a whole rather than either component.

**Three arms, all baseline probes, all forward-only** — `--max-new 8`, no generation, no judging.
Identical config to `p2A`/`tbA`/`p5A_gun`/`wkA`: `natural_doublespeak` × `semantic_forced_choice` ×
`n_examples ∈ {1,2,4,8}`, **48 rows, 12 per dose**, Llama-3.1-8B, `--attn-impl eager`. Nothing retuned.

| arm | bank | what it disconfounds |
|---|---|---|
| **`bbA`** | `basket_bomb` | **codeword held at `basket`, concept → bomb.** The decisive one for R-98. |
| `tkA` | `ticket_knife` | concept `knife` on a second codeword — completes R-101's open item |
| `wbA` | `window_bomb` | concept `bomb` on the `window` codeword — the fourth 2×2 cell |

#### 📌 Conditions, fixed now

Reference: installs = crosses 0.500 and rises (`main` 0.667→1.000, `ticket_bomb` 0.750→1.000,
`window_knife` 0.583→1.000); fails = never crosses (`basket_gun` 0.333→0.417).

1. **`basket_bomb` INSTALLS** → the failure is the **concept `gun`**, not the codeword. R-98's
   sentence must be rewritten as *"the mapping does not install for the `gun` concept"*, and the
   concurrent session's entry-6 reading inherits that narrowing.
2. **`basket_bomb` FAILS** → the failure is the **codeword `basket`**, and R-98's sentence is wrong in
   the other direction — it is not about the concept at all.
3. **AMBIGUOUS** (crosses but flat, or rises without crossing) → reported as such; **R-98's claim is
   downgraded to "does not install, cause unresolved"** rather than being given either story.

**⛔ Pre-committed**: `tkA` and `wbA` are **descriptive** — they fill the 2×2 and settle R-101's open
item, and **no claim rests on them alone.** The decisive arm is `bbA`. **And whatever comes back, the
existing measurement stands**: `basket_gun` does not install. What is at stake is only **why**, and
therefore how far the sentence generalises.

**⚠ Cells are 12 rows** (R-98's standing caveat) — the *shape* is the claim, no single cell is.


### ⛔ C-30 (05:55) — **R-101's 2×2 MIXED JUDGE INVOCATIONS — the exact defect I audited them for in R-82. The conclusion is invariant; the ratio I quoted is not, and it moves 40% between judge draws.**

They reported reading `ticket|bomb` as **27/96** where R-101 used **30/96**. **Both are correct.**
Verified on the artifacts:

| judge dir | ASR |
|---|---|
| `e6j_A_ticket_20260828_011348_3802351` | **27/96** |
| `dpj_A_ticket_20260828_024703_3806910` | **30/96** |
| disagreement on the **same generations** | **7/96 = 0.0729** |

**The same rows, judged twice, differ on 7 of 96** — above the ~0.05 floor DR-10 and their V-7
measured jointly, **and it landed inside a headline cell.**

**R-101 took `ticket|bomb` from a message rather than from the invocation that produced the other three
cells.** So my 2×2 mixed judge invocations. **R-82 is the entry where I audited exactly this and found
every one of my own primary contrasts clean** — and then I built a cross-bank table that wasn't,
because three cells came from `x22_*` and the fourth came from wherever I had last seen it quoted.

**What changes and what does not:**

| | |
|---|---|
| concept effect (mine, 30/96) | +0.240, ratio **≈8×** |
| concept effect (theirs, 27/96) | +0.224, ratio **≈14.3×** |
| **conclusion** | **identical — concept dominates codeword** |
| **the ratio** | **moves ~40% on one cell's judge draw** |

**So the ratio is not quotable at two significant figures.** Adopting their phrasing: **concept
dominates codeword by roughly an order of magnitude.** R-101's "+0.240 against +0.031, roughly 8×" is
**over-precision on a number one re-judge moves by 40%**, and I am recording that rather than quietly
softening it.

**The conclusion is robust precisely because the effect is large**: 0.28-vs-0.05 survives a 7-row
perturbation in any cell. **A smaller effect measured the same way would not have, and nothing in how I
built the table would have told me.**

#### ⛔ And a coordination failure of my own, recorded because it cost GPU

I offered to run `ticket_knife` and `window_bomb` probes *"if you'd rather stay on your judging
queue"*, then **launched them (`788643`, `788644`) before their answer arrived.** They had already
submitted the same two arms as **`788639`/`788640`** — lower job ids, so theirs went first. **Two of my
three PR-34 arms are duplicates.** I do not cancel, so they will run and waste a few GPU-minutes.

**`bbA` (`basket_bomb`) is not a duplicate and is the decisive arm** — it is the one that
disconfounds *my own* R-98, which nobody else is testing. **The waste is real, small, and mine: I acted
on an offer instead of waiting for the reply to it.**


### 🏆 R-102 (06:05) — **PR-34 condition 1 FIRES: `basket_bomb` installs, so R-98's failure is the CONCEPT `gun`, not the codeword. And `ticket_knife` installs too, which COMPLETES R-101's harm-category account.**

Seven banks now have a measured installation ladder, 12 rows per cell:

| bank | codeword | concept | n=1 | n=2 | n=4 | n=8 | total | installs? |
|---|---|---|---|---|---|---|---|---|
| `main` | carrot | bomb | 0.667 | 0.917 | 0.917 | **1.000** | 42/48 | yes |
| `ticket_bomb` | ticket | bomb | 0.750 | 1.000 | 1.000 | **1.000** | 45/48 | yes |
| **`basket_bomb`** | **basket** | **bomb** | 0.667 | 0.833 | **1.000** | **1.000** | **42/48** | **YES** |
| `window_bomb` | window | bomb | 0.667 | 0.917 | 0.833 | 0.917 | 40/48 | yes |
| `window_knife` | window | knife | 0.583 | 0.833 | 0.833 | **1.000** | 39/48 | yes |
| `ticket_knife` | ticket | knife | 0.417 | 0.583 | 0.583 | 0.917 | 30/48 | **⛔ NOT DEMONSTRATED — p=0.111 vs chance (C-31)** |
| **`basket_gun`** | **basket** | **gun** | 0.333 | 0.417 | 0.417 | 0.417 | **19/48** | **NO** |

#### Condition 1 fires — R-98's sentence was wrong in its scope

**`basket_bomb` installs and saturates on the same codeword that fails with `gun`.** So the failure is
**not** the codeword `basket`; it is the **concept `gun`**. PR-34 pre-committed the consequence:

> **R-98's *"the mapping does not install on `basket_gun`"* becomes *"the mapping does not install for
> the `gun` concept"*** — and the concurrent session's entry-6 null reading, which rests on R-98,
> inherits that narrowing.

**All four bomb banks install. Both knife banks install. The single gun bank does not.** Installation
tracks the **concept**, and — as with ASR (R-101) — **the codeword does almost nothing**: `basket`
gives 42/48 with bomb and 19/48 with gun; `ticket` gives 45/48 with bomb and 30/48 with knife.

#### R-101's open item is settled, and the harm-category account is now complete

R-101 left this explicitly unresolved: *"if the knife banks install and still score ~0.05, the
harm-category account is complete; if they do not install, two effects are tangled."*

**They install.** `ticket_knife` **30/48**, `window_knife` **39/48** — and both score **~0.05 ASR**
(0.052, 0.042). **So the knife banks bind the mapping and still almost never produce a successful
attack. Two effects are not tangled: there is one effect (harm category depresses ASR) and one
separate failure (the `gun` concept does not install at all).**

**That completes the account the concurrent session should carry**: `window_knife`'s install/attack
gap is a **harm-category** phenomenon, confirmed on a second codeword.

#### ⚠ What I am not claiming

* **`ticket_knife` is the weakest installer** — 30/48, starting **below chance** at n=1 (0.417) and
  only reaching 0.917 at n=8. It installs, but less completely than the bomb banks. **The binary
  "installs / does not" hides a gradient**, and `basket_gun` is at one end of it rather than in a
  separate category. **PR-34's conditions were written as binary and I am reporting the gradient
  rather than pretending the binary was sufficient.**
* **One model, Llama-3.1-8B.** Nothing here is cross-model.
* **12-row cells.** The *shape* is the claim; `window_bomb`'s non-monotone 0.917 → 0.833 → 0.917 is
  one row wobbling and means nothing.


### ⛔ C-31 (06:10) — **I applied an "installs / does not" threshold at 0.500 without ever testing it against chance. Two of my own statements fail that test: `basket_gun` does NOT prefer the codeword, and `ticket_knife` does NOT demonstrably install.**

R-102 noted the binary hides a gradient and then used the binary anyway. **Testing each bank against
chance (24/48) with an exact two-sided binomial — the check I should have run before writing either
entry:**

| bank | concept | wins | rate | p vs chance | verdict |
|---|---|---|---|---|---|
| `ticket_bomb` | bomb | 45/48 | 0.938 | **1.3e-10** | above chance |
| `main` | bomb | 42/48 | 0.875 | **1.0e-07** | above chance |
| `basket_bomb` | bomb | 42/48 | 0.875 | **1.0e-07** | above chance |
| `window_bomb` | bomb | 40/48 | 0.833 | **3.3e-06** | above chance |
| `window_knife` | knife | 39/48 | 0.812 | **1.5e-05** | above chance |
| **`ticket_knife`** | knife | 30/48 | 0.625 | **0.111** | **INDISTINGUISHABLE** |
| **`basket_gun`** | gun | 19/48 | 0.396 | **0.193** | **INDISTINGUISHABLE** |

#### Two statements of mine are wrong, in opposite directions

**1. R-97 said of `basket_gun`: *"The model prefers the codeword to the concept on this bank before any
intervention."*** **It does not.** 19/48 is **p = 0.193** against chance — the mapping is **absent**,
not **inverted**. "Prefers the codeword" claims a direction the data does not support, and the
difference matters: *no mapping installed* and *an anti-mapping* are different phenomena.
**Corrected to: indistinguishable from chance.**

**2. R-102 listed `ticket_knife` as "installs (weakest)" at 30/48.** **p = 0.111 — not demonstrably
installed either.** I put it in the installs column because 0.625 > 0.500, **which is exactly applying
a threshold below the measurement floor** — the failure the standing review item names.

#### What this costs the harm-category account

R-102 completed R-101's open item with *"the knife banks install and still score ~0.05"* — **plural**.
**Only `window_knife` qualifies** (39/48, p = 1.5e-05, ASR 0.042). `ticket_knife` neither supports nor
contradicts it; it is uninformative on installation.

**So the account rests on ONE bank, not two.** It is still a real instance — `window_knife` installs
solidly and scores 0.042 — but **"both knife banks" was overstated and the second codeword I claimed
as confirmation is not confirmation.** The concurrent session should carry the singular.

#### What survives untouched

**PR-34's decisive result is unaffected**: `basket_bomb` at 42/48 is **p = 1.0e-07** above chance,
against `basket_gun`'s indistinguishable 19/48 **on the same codeword**. **The concept-not-codeword
conclusion rests on a comparison where one side is overwhelming and does not depend on where the other
side sits relative to chance.** Likewise all four bomb banks and `window_knife` are far past any
threshold question.

**The lesson is the one I keep relearning tonight**: I checked whether the *effect* was above a
threshold and never whether the *threshold* was resolvable. **A 48-row binary readout cannot separate
0.625 from 0.500, and nothing about the number's appearance says so.**


### ⛔ C-32 (06:40) — **The remedy I proposed for C-31 is not available and would not have worked. `ticket_knife` is UNRESOLVABLE on this bank, and I checked that only after recommending a run.**

C-31 closed by telling the concurrent session that **"96 rows would put p<0.05 within reach of a 0.625
effect"** and that *"the population size, not the model, is what makes `ticket_knife` unresolvable."*
**Both halves are wrong, and I established that by counting rows I could have counted first.**

**96 rows do not exist.** `ticket_knife` has **288** forced-choice rows, **72 per condition**, and
`natural_doublespeak` splits **12 per dose across n ∈ {0,1,2,4,8,16}**. So:

| population | rows | note |
|---|---|---|
| what I ran, `n ∈ {1,2,4,8}` | **48** | |
| **ceiling with demonstrations**, `n ∈ {1,2,4,8,16}` | **60** | adding `n=16` is the only headroom |
| 72 | 72 | **only by including `n=0`, which teaches no mapping** — it would dilute the thing being measured |
| **96** | — | **does not exist on this bank/condition** |

**And the reachable ceiling would not have settled it.** Power to detect a true rate of 0.625 at
α = 0.05:

| n | k needed | expected at 0.625 | **power** |
|---|---|---|---|
| 48 | 32 | 30.0 | **0.331** |
| **60 (the ceiling)** | 39 | 37.5 | **0.399** |
| 96 *(unreachable)* | 59 | 60.0 | 0.627 |
| 144 | 85 | 90.0 | 0.828 |

**At the maximum population this bank can supply, power is 0.399** — a coin flip whether a real 0.625
effect registers. **Even my unreachable 96 gives only 0.627.** Resolving `ticket_knife` would need
**~144 rows**, i.e. **three times the natural_doublespeak forced-choice population that exists**.

#### The correction, and what it changes

**`ticket_knife`'s installation is not "unresolved pending a bigger run" — it is unresolvable with this
bank.** C-31 recorded it as indistinguishable from chance; **that verdict stands and is now known to be
permanent** rather than provisional. The harm-category account rests on `window_knife` alone
(39/48, p = 1.5e-05) **and will continue to**, unless someone builds a larger probe population, which
is a bank-design change and not a rerun.

**What I did wrong is narrow and worth naming**: I diagnosed an underpowered measurement correctly and
then **prescribed a remedy without checking the prescription against the same constraint I had just
measured.** The row count was one `Counter` away and I sent the advice first. **Same tick, opposite
halves: rigorous about the finding, casual about the recommendation.**

**⚠ Sent to them immediately** — they had the arm as a live option and it cannot answer the question.


### ⛔ C-33 (07:15) — **Auditing my own prescriptions, as the concurrent session's framing suggested, found a second under-specified one: R-97's pre-screen criterion would have PASSED `ticket_knife` — the exact bank C-31 later showed is indistinguishable from chance.**

They made the sharp observation behind C-32: **"prescriptions don't get audited the way findings do,
because they don't look like claims."** Every other correction tonight was a claim about data that a
cheap check refuted; C-32 was a claim about what a **future run** would show, which no existing data
could refute. **So I audited the other prescriptions I have issued this session.** One fails.

**R-97 gave the peer a screening rule for picking the next bank**: *"baseline mapped-wins must clear
chance by a real margin ... one baseline probe arm per candidate, no intervention needed."* **"A real
margin" is not a number**, and the natural reading is "above 0.500". Tested at n = 48:

| bank | wins | naive "> 0.500" | tested p < 0.05 | |
|---|---|---|---|---|
| `ticket_bomb` … `window_knife` | 45–39/48 | PASS | PASS | agree |
| **`ticket_knife`** | **30/48** | **PASS** | **fail** | **screen MISLEADS** |
| `basket_gun` | 19/48 | fail | fail | agree |

**The smallest count that clears p < 0.05 at n = 48 is 32/48 = 0.667.** My screen, read the obvious
way, admits everything above 24/48 — **including a bank whose installation cannot be established at any
population this design supports (C-32).** Anyone applying it would have selected `ticket_knife` as a
suitable candidate and then discovered, as I did, that it can never answer.

**Corrected criterion, stated as a number rather than a sentiment**: a candidate bank passes the
pre-screen only if baseline mapped-wins **≥ 32/48 (0.667)**, i.e. p < 0.05 against chance on the
population that will actually be used. **At other population sizes the threshold moves and must be
recomputed, not carried over** — at n = 60 it is 39/60, at n = 96 it is 59/96.

#### Why this one was invisible and the findings were not

Every finding in this log carries numbers that another session can recompute — and several have been
recomputed, by them and by me. **A prescription carries no numbers to check.** "Clear chance by a real
margin" reads as rigour precisely because it names the right concept; **it fails because it never
names the threshold, and nothing about it looks incomplete.**

**Two prescriptions of mine have now failed in two ticks** — C-32 (a remedy that does not exist and
would not have worked) and C-33 (a screen that admits the case it was designed to exclude) — **against
zero failed findings in the same window.** That asymmetry is the finding, and it is theirs, not mine:
**I audit what I assert and not what I advise.**

**Sent to them immediately**, since they adopted the screen.


### ✅ R-103 (07:15) — **C-31/C-33 corrected readings and advice; the PRE-REGISTRATIONS carried the same unresolvable criterion. Re-evaluated against a powered threshold — every decisive verdict survives, and I am recording the check rather than assuming it.**

C-31 caught that "crosses 0.500" is below the resolvable floor on 48 binary rows, and C-33 caught the
same defect in a screening rule I gave the peer. **Both fixed the output. Neither fixed the input** —
**PR-33 and PR-34 wrote their conditions as *"crosses 0.500 and rises"* / *"never reaches 0.500"*, so
the pre-registrations themselves specified a threshold the population cannot resolve.**

**A pre-registration with an unresolvable criterion is a latent defect even when the answer clears it
comfortably**, because it would have licensed a verdict on a marginal case. So I re-evaluated every
verdict under the properly powered rule — **k ≥ 32/48 (0.667), exact binomial p < 0.05:**

| pre-reg | bank | verdict as written | wins | p | under the powered rule |
|---|---|---|---|---|---|
| **PR-33** | `window_knife` | INSTALLATION | 39/48 | **1.5e-05** | **SURVIVES** |
| **PR-34** | `basket_bomb` | INSTALLS *(decisive)* | 42/48 | **1.0e-07** | **SURVIVES** |
| R-98 | `basket_gun` | non-installation | 19/48 | 0.193 | **SURVIVES** (not above chance) |
| PR-34 | `ticket_knife` | *descriptive only* | 30/48 | 0.111 | n/a — pre-committed as carrying no claim |
| PR-34 | `window_bomb` | *descriptive only* | 40/48 | 3.3e-06 | n/a — same |

**Every verdict that carried a claim survives.** PR-33's and PR-34's decisive arms clear the powered
threshold by four and six orders of magnitude respectively, and R-98's negative verdict is *"not
distinguishable from chance"*, which is what the tested rule also says.

**The two arms that fall in the unresolvable band were both pre-committed as descriptive** — PR-34
stated *"`tkA` and `wbA` are descriptive… no claim rests on them alone"* before the data existed.
**That pre-commitment is the only reason `ticket_knife`'s 30/48 never became a claim**, and it was
luck of drafting rather than foresight about power: I wrote it to protect against over-reading
side-arms, not because I had computed anything.

**The correction for future pre-registrations, stated as a rule**: an installation-style criterion must
name **a count and a test**, not a rate — *"k ≥ 32 of 48, exact binomial p < 0.05"* rather than
*"crosses 0.500"* — and the count must be **recomputed for the population actually used**, since it is
39/60 at n = 60 and 59/96 at n = 96. **The threshold is a property of the population, not of the
question**, which is exactly what "0.500" hides.

**No claim changes. What changes is that the criterion is now checkable**, and the check has been run
rather than assumed.

---

*Opened 2026-08-25 00:30 at HEAD `059e819f`. Part A is stable. Everything below it is append-only.*

---

### 🔬 DR-14 (07:47) — **Deep review. Full suite green; all four PR-33/34 headlines reproduce exactly from raw rows; C-32's population and power arithmetic verified and shown to be structural to every bank. Two defects found: the corrections ledger had silently stopped propagating, and my own installation verdicts had never been produced by a committed artifact.**

**Queue empty, no FAILED/CANCELLED, tree clean.** Full suite **1217 passed, 7 skipped** (245s).

#### 1. Independent recomputation — all four headlines reproduce

Recomputed from `results.jsonl` rather than from any prior summary, at
`outputs/boombness/score_behavior/{wkA_20260828_042130_2251980, bbA_20260828_054201_3951828, tkA_20260828_054201_3951916, wbA_20260828_054231_3952502}`:

| bank | wins | p vs chance | ties | doses | gate | failed rows |
|---|---|---|---|---|---|---|
| `window_knife` | **39/48** | 1.52e-05 | 0 | 12/12/12/12 | PASS | 0 |
| `basket_bomb` | **42/48** | 1.01e-07 | 0 | 12/12/12/12 | PASS | 0 |
| `ticket_knife` | **30/48** | 0.111 | 0 | 12/12/12/12 | PASS | 0 |
| `window_bomb` | **40/48** | 3.31e-06 | 0 | 12/12/12/12 | PASS | 0 |

All four on `Llama-3.1-8B-Instruct`, arm `A_baseline`, `intervention=None`, single condition
`natural_doublespeak`, each reading its **own** bank file, 48/48 rows succeeded. **Zero ties**, so the
strict-`>` predicate is not carrying hidden mass. Four **distinct** content hashes and a single write
per dir — no silent overwrite. `check_all.py` **6/6**.

#### 2. C-32 verified, and it is structural rather than specific

The population and power table now recomputed from the bank files themselves. Every one of the **five**
banks has the identical structure — **72** `natural_doublespeak` × `semantic_forced_choice` rows,
**12 per dose over n ∈ {0,1,2,4,8,16}**, hence **48 run and 60 the ceiling with demonstrations, and 96
does not exist**. Power at a true 0.625: **0.331 (n=48), 0.399 (n=60)**, 0.627 (96), 0.828 (144);
critical counts **32/48, 39/60, 59/96, 85/144**. Every figure C-32 and C-33 quote reproduces exactly.
**The unresolvability is a property of the bank design, not of `ticket_knife`** — any 48-row cell here
misses a real 0.625 effect two times in three.

#### 3. ⛔ Defect found: the corrections ledger had stopped propagating

**C-32 and C-33 were in this log and absent from the deliverable's corrections table** — the first
gap since the table was created. Both were written the same night I stopped opening new work, which is
exactly when a ledger stops being re-read. **Fixed**: both rows added to
`reports/SPRINT_SUMMARY_2026-08-25_BEHAVIORAL_CAUSALITY.md`; **C-19…C-33 now all present, verified by
count.**

#### 4. ⛔ Defect found: no artifact ever carried the floor

Every other headline this sprint is emitted by a **script that writes a JSON artifact with its
pre-registration embedded**. The installation counts were the exception: I computed them **ad hoc in a
shell one-liner each tick**. `grep -rl mapped_wins src/boombness/*.py` returns **one** file, and it is
the bridge, which does something else. **That absence is the mechanism behind C-31 and C-33** — a
fraction with no artifact has nowhere to carry its threshold, so "0.625 > 0.500" looked like a reading
rather than a judgement.

**Fixed**: `src/boombness/mapping_installation_verdict.py` — classifies **only** against
`critical_k(n, α)` recomputed for the n actually used, reports the design's **power** so an
unresolvable cell reads as unresolvable rather than as a null, refuses a run whose `option_mass_gate`
is not PASS or that has failed rows, and refuses duplicate labels. Re-ran on all four probes
(`outputs/boombness/mapping_installation_verdict/pr33_34_install_20260828_074724_800265/`) —
**reproduces R-103 exactly**: three INSTALLED, `ticket_knife` NOT_ESTABLISHED.

### ⛔ C-34 (07:47) — **Writing the rule down made two of my own words wrong: `basket_gun` does not reach the lower tail, and I had named that tail "ABSENT" when it means "INVERTED".**

The new test asserting C-31's reading failed — **and the test was the thing that was wrong**, which is
how I found the rest.

* **C-31 said `basket_gun` 19/48 is "the mapping is ABSENT, not inverted".** Under the rule I had just
  written, the lower tail at n=48 needs **≤ 16**. **19 does not reach it.** So `basket_gun` is
  **NOT_ESTABLISHED — the same verdict as `ticket_knife`**, and it licenses **no positive claim of
  absence**. C-31 corrected R-97's over-reading in one direction and then made a milder version of the
  same over-reading in the other.
* **My verdict label was misnamed.** Significantly *below* chance means the model **prefers the
  codeword** — that is an **inverted** mapping. Calling that tail `ABSENT` would have let exactly the
  claim C-31 made be read straight off the artifact. **Renamed `ABSENT` → `INVERTED`.**

#### What survives, and it is stronger than what it replaces

**PR-34's decisive contrast never depended on either label**, and I had never run the test that
actually carries it. As a **two-sample** comparison on the same codeword:

| contrast | counts | Fisher exact |
|---|---|---|
| **`basket_bomb` vs `basket_gun`** (concept swapped, codeword held) | 42/48 vs 19/48 | **p = 1.64e-06** |
| `window_knife` vs `ticket_knife` (codeword swapped, concept held) | 39/48 vs 30/48 | p = 0.0683 |
| `window_bomb` vs `window_knife` | 40/48 vs 39/48 | p = 1 |

**PR-34 stands on p = 1.64e-06**, and that is the correct test for it — a between-bank contrast, not
two one-sample labels compared by eye. The second row is **not significant**, which is consistent with
C-31's finding that the codeword-side account rests on one bank and adds nothing new.

**The pattern across C-31 → C-34 is one thing**: I keep reading a *label* off a one-sample cell when
the claim is a *contrast*. The fix is now in code — `INVERTED`/`NOT_ESTABLISHED` are distinct verdicts
in an artifact, and 10 tests in `tests/test_mapping_installation_verdict.py` assert on **behaviour**,
not on module wording (C-27), so a reintroduced 0.500 cut fails the suite rather than reading fine.

---

### ✅ R-104 (08:10) — **Swept the live claims for C-34's fault pattern rather than fixing only the instance that produced it. One claim was carrying it: C13's model-specificity had never been tested as an interaction. It survives, conservatively.**

C-34 named a recurring fault — **reading a label off a one-sample cell when the claim is a contrast** —
and DR-14 fixed the single case that exposed it. **A fault named once and fixed once is not closed**, so
I checked every live claim for the same shape. The sweep is cheap: a claim has the shape iff its
*statement* is a comparison and its *evidence column* holds two independent one-sample results.

| claim | comparison in the statement | how it is evidenced | verdict |
|---|---|---|---|
| C1 | `demoproc` **vs the other three scopes** | +0.1625 vs baseline, others at **exactly zero** — gap 0.1625 against the **arm-vs-arm** 0.0417 (≈3.9×) | sound, the between-arm margin is the one applied |
| C3 | the four scopes vs **each other** | all pairwise gaps vs 0.0417 | sound, explicitly pairwise |
| C7 | Qwen3 yes / Llama **declined for power** | R-52 declines rather than claims a difference | sound, no contrast asserted |
| C11 | Qwen3 **replicates** Llama | same-direction agreement, no difference claimed | sound |
| C6 | "Llama only" | population, not a contrast — Qwen3 untested | sound |
| **C13** | **"LLAMA-SPECIFIC"**, Qwen3 "tested and NEGATIVE" | **two separate one-sample results** | ⚠ **the C-34 shape** |

#### C13 tested properly, and it holds

"Significant in Llama, not significant in Qwen3" is **not** the same statement as "Llama differs from
Qwen3", and only the second is what C13 claims. Recomputed from the row counts in the claim table:

| cell | counts | Δ | Fisher |
|---|---|---|---|
| Llama, base → longpre12 | 27/160 → **6/160** | −0.1313 | p = 1.54e-04 |
| Llama, base → longpre10 | 27/160 → **7/160** | −0.1250 | p = 4.16e-04 |
| Qwen3, base → preamble | 21/160 → **23/160** | +0.0125 | p = 0.871 |

**The interaction — the difference of the two differences, which is the claim:**

| contrast | dd | z | **p** |
|---|---|---|---|
| Llama[longpre12] vs Qwen3 | **−0.1437** | −2.83 | **0.0047** |
| Llama[longpre10] vs Qwen3 | **−0.1375** | −2.69 | **0.0072** |

**C13's model-specificity survives**, and the test is **conservative**: the within-model comparisons are
**paired** — `tests/test_preamble_is_the_only_difference` verifies the banks differ **only** by the
preamble across 200/200 rows, so the same 160 prompts appear on both sides — and I used the **unpaired**
variance, which inflates the SE. A paired treatment can only reduce these p-values.

**No claim changes.** What changes is that C13 is now evidenced by the test its own wording requires,
and the fault C-34 named has been checked against the whole ledger instead of the one cell that
happened to expose it. **Five of six claims were already sound; the one that was not, survives.**

---

### ✅ R-105 (09:10) — **A concurrent job failed hard and became the first real test of yesterday's guard. It refused correctly — and refusing it exposed a gap the guard did not cover: silent attrition would have adapted the threshold instead of tripping it.**

**Job 789095 (not mine — the concurrent session's `q5A_lpQ14B`, Qwen3-14B) FAILED.** I did not launch it,
did not cancel it and have not touched it; the diagnosis below is only because it writes into the
shared `outputs/` tree and because it is the first degraded run my new instrument has ever met. Two
independent failures, both theirs to resolve:

1. **CUDA OOM on 92 of 160 rows** — `n_succeeded=68`, surviving by query kind
   `{semantic_one_word: 37, semantic_forced_choice: 18, comprehension_usage: 13}`.
2. **Tail gate FAILED** on two kinds: `comprehension_usage` median option mass **0.001466** and
   `semantic_one_word` **0.01854**, both under the 0.05 gate. `semantic_forced_choice` **passed**
   (median 0.9998), so the forced-choice arm looks individually healthy.

**`src/boombness/mapping_installation_verdict.py` refused it**, on `option_mass_gate` being the
`OVERRIDDEN — NOT REPORTABLE` string rather than `PASS`. The `n_failed=92` check would have caught it
independently. **First live exercise, correct refusal.**

#### ⚠ But the refusal fired for the wrong reason to be reassuring

`semantic_forced_choice` **passed its own mass gate**, and the run dir is written and inviting. The
guard stopped it via two conditions that happen to be true here — **neither of which is about the
forced-choice population itself.** A run that was forced-choice-only, gate PASS, and simply lost rows
would have walked straight through, because **`n` is taken from the rows on disk**: the population
shrinks, `critical_k` **quietly shrinks with it**, and the verdict still prints as valid. At the n this
job actually produced:

| n | `critical_k` | as a rate | power @ 0.625 |
|---|---|---|---|
| **18** (surviving forced-choice) | **14** | **0.778** | **0.135** |
| 48 (intended) | 32 | 0.667 | 0.331 |

**This is C-33's shape arriving through the data rather than through prose** — a threshold that silently
re-fits itself to whatever population survived. And it is **worse than lost power**: the attrition here
is **OOM, which is length-correlated**, so the survivors are systematically the **shorter prompts**. A
fraction computed on them is not an estimate of the bank's rate at all.

**Guard added**: the tool now refuses when `n_result_rows < n_bank_rows`, with the reason stated —
the survivors of length-correlated attrition are not a random subset. **Two tests**, and deliberately
one of each polarity: a silently-attrited fixture (gate PASS, `n_failed=0`, 48 of 160) is **refused**,
and a complete 48/48 fixture is **accepted and returns INSTALLED**. The positive test is the point —
C-26 recorded that a guard which passes for the wrong reason is worthless, so this one is pinned on
both sides. **12 tests pass.**

**Re-verified after the change**: all four PR-33/34 runs still accepted and **unchanged** — 42/48, 39/48,
40/48 INSTALLED and 30/48 NOT_ESTABLISHED, `crit=32` throughout. `check_all` 6/6.

**No claim moves.** What moves is that the instrument was tested against a real failure instead of only
against fixtures I wrote, and the failure taught it something my fixtures had not.

---

### ✅ R-106 (10:10) — **The concurrent session's V-54 (the option-mass gate can advertise PASS over a NaN readout) lands directly on my instrument, which trusted that gate and used a predicate NaN escapes. My four verdicts are clean — checked, not assumed — and the tool no longer depends on someone else's gate.**

They committed **V-54** (`3ec553da`): **`option_mass_gate` advertised PASS over a ~90% NaN readout,
because NaN escapes BOTH sides of a threshold** — `x < gate` and `x >= gate` are each False, so a
comparison-based gate cannot see it. That is their finding on their branch; it is load-bearing for me
for two reasons I had not considered:

1. **My provenance check trusts exactly that field.** `mapping_installation_verdict.py` refuses a run
   whose `option_mass_gate != "PASS"` — i.e. it takes an upstream gate's word for the soundness of a
   claim **this tool** is making.
2. **My win predicate has the same hazard.** `p_concept > p_codeword` is **False** for NaN, so a NaN row
   is silently counted as **"not a win"** — it does not error, it **depresses the fraction**, which
   would move a verdict toward NOT_ESTABLISHED while everything still looked healthy.

#### First: are the verdicts affected? No — and I checked rather than assuming

All four PR-33/34 runs, every row:

| bank | n | NaN `p_concept` | NaN `p_codeword` | missing | wins |
|---|---|---|---|---|---|
| `window_knife` | 48 | 0 | 0 | 0 | 39 |
| `basket_bomb` | 48 | 0 | 0 | 0 | 42 |
| `ticket_knife` | 48 | 0 | 0 | 0 | 30 |
| `window_bomb` | 48 | 0 | 0 | 0 | 40 |

**0 non-finite or missing values across all 192 rows**, and the win counts reproduce exactly. **The
verdicts stand: 42/48, 40/48, 39/48 INSTALLED and 30/48 NOT_ESTABLISHED, `crit=32`.**

#### Second: the instrument was still wrong to depend on the gate

A clean result does not make an unsound check sound. **Added a finiteness guard that verifies the
values this tool actually uses**, rather than inheriting a verdict from a gate that V-54 has just shown
can be mistaken. Two tests: a fixture with one NaN is **refused** with `non-finite` named, and a second
test pins **why** the guard is needed by asserting the hazard itself — `nan > 0.5` and `nan < 0.5` are
**both False**, so without the guard the row changes the count instead of raising.

**Re-verified after the change**: all four runs still accepted, all four verdicts **byte-identical**.
**14 tests pass**, `check_all` 6/6.

**The transferable point is not about NaN.** My tool had three provenance checks and **all three
delegated** — `option_mass_gate`, `n_failed`, `n_result_rows` are fields someone else computes. R-105
added the third after a real failure; V-54 shows the first can be wrong. **A guard that only reads
other people's verdicts inherits their blind spots**, so the values a claim rests on are now checked
where the claim is made.
