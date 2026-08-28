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
as much attack, and on Qwen3 more. The concept binding **survives** the intervention on both models.
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
| C1 | `demo_processing_only` restores refusal; no other scope does | Llama + Qwen3, **2 independent pools, 2 CODEWORDS** (R-73: `basket` **+0.1250**, other three scopes at **exactly zero** refusals; **truncation-robust — R-75**: re-run at a 640-token cap with 0.000 truncation gives **the identical +0.1250 on the SAME 14 rows** while 81/96 completions changed) | d10 behavioural, natural_doublespeak | 160 × 3 settings | prompt (rate), domain (sign) | **+0.1625** (Llama/A), **+0.1312** (Qwen3/A), **+0.1938** (Llama/B) | vs `MARGIN_VS_BASELINE` 0.0521; PR-6 3/3 **and** PR-12 2/2 | attn knockout, demo→demo prefill | 3 other scopes, all within margin | **CONFIRMATORY** |
| C2 | Refusal restoration is **not** the route to attack removal | Llama + Qwen3 | same | 160/model | prompt, dose-matched **and causally, both models** | Llama n=4 gaps **0.0000**; Qwen3 n=8 refusal arm **worse**; **R-35/36/37/38 — a COMPLETE 2x2 (model family x demonstration pool): refusal rows removed 18 / 17 / 12 / 18 against an 8.3-row margin (2.16x / 2.04x / 1.44x / 2.16x), while the below-band control moves it by exactly 0 rows in all four. As percentages of the rise: 69.2 / 81.0 / 92.3 / 58.1% — but those are INVERTED relative to the evidence (DR-5), because a near-zero clean baseline inflates the ratio** | arm-vs-arm 0.0417 | same | zero-refusal arms; below-band L5 patch | **R + CAUSAL** |
| C3 | The four scopes remove indistinguishable amounts of attack | Llama + Qwen3 | same | 160/model | prompt | all pairwise gaps ≤ 0.0417 except marginal `qpre` pairs | arm-vs-arm 0.0417 | same | each other | **R** |
| C4 | Attack removal proceeds by **coherent non-compliance**, not degeneration | Llama + Qwen3 | killed attacks | 165 across 8 cells | killed row | **0** degenerate rows; `frac_scorable` 1.000 | `coherence_gate` thresholds, mutation-verified | same | positive/negative detector controls | **R** |
| C5 | Concept binding **survives** the intervention — **`demo_processing_only` scope; bank restriction LIFTED (R-93)**: preserved on `main` (0.5416→0.6021) **and** `ticket_bomb` (45/48→45/48) where the **unscoped** mask collapses it (45/48→**15/48**). The scope, not the bank, is what destroys binding | Llama (2 banks) + Qwen3 (1 bank) | forced-choice probe | 48 families/model — **`core2x2` ONLY (C-24)**: the probe was never generated for the other six blocks, so 396 of 468 behavioural family stems have no probe side and cannot join. Scope, not validity | family (within-family 2×2) | Llama 0/48 binding lost; Qwen3 0/10 killed lost | McNemar / contingency | same | `legacy` loses 28/48 (Qwen3) | **R** |
| C6 | Refusal restoration scales with demonstration count | **Llama only** | d10, by `n_examples` | 40/cell | prompt | +0.0000 → +0.3500, monotone | endpoint vs 0.0521, 6.7× | same | `legacy`/`respq` flat at ≤0 | **S** |
| **C7** | **Attack removal is DEMONSTRATION-SPECIFIC** | **Qwen3-14B** (Llama **declined for power**, not refuted — R-52) | `longpreQ14`, `n_examples` **4 and 8** | 40/dose; **5 and 7** baseline attacks | prompt, **3 independent draws** | `demoproc` removes **5/5** and **5/7** attacks (−0.1250 each); controls remove **1,2,2** and **2,−2,−1**, all within ±0.0521 — ⚠ but pool A's `d2`/`d3` were judged in a **separate invocation** from their baseline and their 1-2 row readings sit at the ~2-row judge floor (**R-82**), so the pool B replication carries that leg. **Quantified (R-83)**: against a per-arm judge floor those two cells are **0.00× and 0.38×** the paired noise SD, while pool B's effect is **3.6×** (−9 rows vs SD 2.52); separation **2.0×** and **3.2×**. **Pool B (R-62): −4/4 and −5/6, controls +1,+1,+1 and 0,−1,−2, separation 3.0× and 1.8×**. **Untruncated at a 640-token cap (R-64): −3/4 and −7/7, control +1 and +0, separation 2.4× and 4.2×** | PR-23, committed before the bank existed; all three conditions at **both** doses | `demo_processing_only` 7-17 | **strict count-matched non-demo mask, `match_ratio` 1.000 on all 480 control rows**, 3/3 distinct draws | **S → RESOLVED** (single-model; **replicated on a 2nd pool** R-62; **truncation-robust** R-64) |
| C8 | `query_prefill_only` is a measured null | Llama | d10 | 160 | domain | −0.0250, p=0.6875 | sign test, floor 0.0312 | attn knockout, query prefill rows | other scopes | **S** (negative) |
| **C9** | **Handing back the clean demonstration activations at the top of the knockout band gives back the REFUSAL and not the ATTACK** | Llama + Qwen3, **2 pools** | d10 / d10-poolB behavioural | 160 × 4 cells | prompt | refusal rows removed **18 / 17 / 12 / 18** vs an **8.3-row margin** (1.44-2.16x); as % of rise 58-92%, **inverted relative to the evidence — see DR-5**. ASR: Llama Outcome **C** (null, recovers 16.7%) | vs `MARGIN_VS_BASELINE` 0.0521; PR-13 / PR-14 / PR-16, each committed before its data | per-position `DonorPatch` at L14 (Llama) / L17 (Qwen3), donor = clean forward, same `templated_r` | ~~below-band L5 patch: refusal EXACTLY 0.0000 in all four cells~~ **WITHDRAWN (C-20): that arm is byte-identical to knockout-only on 160/160 rows — a no-op by construction, not a control. C9's specificity leg is unsupported; its primary effect stands**; identity control (`--rescue-donor self`) 8/8 byte-identical | **CONFIRMATORY (4/4)** |
| **C13** | **Neutral context that touches neither the demonstrations nor the query suppresses the doublespeak attack — LLAMA-SPECIFIC** | Llama only (**Qwen3 tested and NEGATIVE**: 21/160 → 23/160, +2 rows, powered, 0 drift — R-54) | d10 vs longpre12 vs longpre10 baselines, same judging window | 160 each | prompt | **27/160 → 6/160 and 7/160**, i.e. **−21 and −20 rows** vs an 8.3-row margin (~2.5×) | PR-21, committed before the re-judge; cross-session drift measured at **2-4 rows** on identical completions | ~10 neutral sentences prepended **outside `demo_block`** | banks verified to differ **only** by the preamble (200/200 rows, `tests/test_preamble_is_the_only_difference.py`) | **S** (single-model) |
| C12 | **The demo/query contrast is position IDENTITY, not position count — but demo-patch magnitude also scales with count** | Llama | d10, `n_examples`=8 | **40** | prompt | at **24 positions each**: demo removes **4** refusal rows and **0.0000** ASR; query removes **13** and **+0.0500** ASR. 24 of ~114 demo positions = **36.4%** of the full effect | PR-18; ⚠ margin is **2.1 rows** at n=40 | size-matched seeded `DonorPatch` draw | ~~below-band L5, exactly inert (15→15)~~ **WITHDRAWN (C-20): byte-identical to knockout-only on 40/40 rows — vacuous, not inert** | **S** (single-model, thin) |
| C11 | **The attack damage is reachable from the QUERY span but not from the demonstration positions — and the query patch is NOT selective** | Llama (**refusal half + dissociation REPLICATE on Qwen3, R-70: −0.09375 (−15/160), 71.4% of the rise, dissociation 0.0875; ASR half DECLINES for power, −0.0062**) | d10 behavioural | 160 | prompt | query ASR **+0.0563** (clears margin by 0.7 rows; **the cited control is withdrawn — C-20**) but only **37.5%** recovery; query refusal **−0.1562** (96.2% of the rise, back to within margin of clean) | PR-17, committed before the arms | `DonorPatch` at L14 over `query_span_positions` (24 positions) | ~~below-band L5 query patch: refusal 0.0000, ASR +0.0125~~ **WITHDRAWN (C-20): byte-identical to knockout-only on 160/160 rows. The +0.0125 is judge non-reproducibility on identical text (2/160), not an effect** | **S** (single-model) |
| C10 | The rescue instrument writes exactly what it read | Llama | smoke | 8 | row | identity vs arm **8/8 identical**; rescue vs identity **0/8** | byte comparison | `--rescue-donor self` | the two comparisons jointly exclude "never fired" | **verified** |

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
| 1 | Caused by response-query retrieval, or by prefill corruption? | **Neither exclusively.** All four scopes remove indistinguishable amounts (C3). The prefill/demo scope is distinguished only by **restoring refusal** (C1). |
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
