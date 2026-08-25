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

## 2. Strongest result

**`demo_processing_only` uniquely restores refusal, across two model families, measured with a
deterministic instrument.** Refusal here is `judge_boombness.kw_refusal` — a keyword detector, **not
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

## 3. ⛔ Retracted / withdrawn — DO NOT REVIVE

| # | Claim that must not be repeated | Why | Ref |
|---|---|---|---|
| 1 | *"`demo_processing_only` works BY restoring refusal"* | At matched dose, zero-refusal arms remove the same attack (Llama n=4: **−0.1750 / −0.1750 / −0.1750**, gaps 0.0000). On Qwen3 n=8 the refusal-restoring arm removes **less** (−0.1500 vs −0.2000). | **C-12 / R-23** |
| 2 | *"`response_query_only` is a weak partial (46% of legacy)"* — Outcome B | Does not replicate at k=10: respq is **85%** of legacy, gap **0.0188**, passing the same pre-registered margin it failed at k=6. | **R-19** |
| 3 | Any **ranking** of the three effective arms by ASR | Gaps demoproc-vs-legacy **0.0250** and legacy-vs-respq **0.0188** are inside the pre-registered **0.0417** margin. Ranking below the instrument's reproducibility is the error the margin exists to prevent. | **C-11** |
| 4 | *"The mapping stops being used when the attack dies"* | Concept-term usage is **confounded with the outcome** — killed rows (0-11%) match baseline **non-jailbroken** rows (6%/10%). In this bank "mentions bomb" ≈ "is a jailbreak". | **R-27** |
| 5 | Dose-response as a **cross-model** mechanism | Confirmed on Llama (+0.0000 → +0.3500, monotone, 6.7× margin) but **refuted on Qwen3** by the pre-registered endpoint rule (+0.0250, within margin). | **R-22** |
| 6 | `d_surface` as an attack objective | Closed earlier in the sprint; not reopened. Gate in §7 remains **BLOCKED**. | prior phase |

## 4. Paper-level claim table (§19-D)

Status key: **R** replicated (2 models) · **S** single-model · **N** evaluated negative · **U** unresolved/untestable.

| # | Claim | Model(s) | Population | n | Independence unit | Effect | Test / margin | Intervention | Control | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 | `demo_processing_only` restores refusal; no other scope does | Llama + Qwen3, **2 independent pools** | d10 behavioural, natural_doublespeak | 160 × 3 settings | prompt (rate), domain (sign) | **+0.1625** (Llama/A), **+0.1312** (Qwen3/A), **+0.1938** (Llama/B) | vs `MARGIN_VS_BASELINE` 0.0521; PR-6 3/3 **and** PR-12 2/2 | attn knockout, demo→demo prefill | 3 other scopes, all within margin | **CONFIRMATORY** |
| C2 | Refusal restoration is **not** the route to attack removal | Llama + Qwen3 | same | 160/model | prompt, dose-matched **and causally, both models** | Llama n=4 gaps **0.0000**; Qwen3 n=8 refusal arm **worse**; **R-35/R-36: one patch removes 69.2% (Llama) / 81.0% (Qwen3) of the refusal rise, both >2x margin, while the below-band control moves it by 0.0000 on both** | arm-vs-arm 0.0417 | same | zero-refusal arms; below-band L5 patch | **R + CAUSAL** |
| C3 | The four scopes remove indistinguishable amounts of attack | Llama + Qwen3 | same | 160/model | prompt | all pairwise gaps ≤ 0.0417 except marginal `qpre` pairs | arm-vs-arm 0.0417 | same | each other | **R** |
| C4 | Attack removal proceeds by **coherent non-compliance**, not degeneration | Llama + Qwen3 | killed attacks | 165 across 8 cells | killed row | **0** degenerate rows; `frac_scorable` 1.000 | `coherence_gate` thresholds, mutation-verified | same | positive/negative detector controls | **R** |
| C5 | Concept binding **survives** the intervention | Llama + Qwen3 | forced-choice probe | 48 families/model | family (within-family 2×2) | Llama 0/48 binding lost; Qwen3 0/10 killed lost | McNemar / contingency | same | `legacy` loses 28/48 (Qwen3) | **R** |
| C6 | Refusal restoration scales with demonstration count | **Llama only** | d10, by `n_examples` | 40/cell | prompt | +0.0000 → +0.3500, monotone | endpoint vs 0.0521, 6.7× | same | `legacy`/`respq` flat at ≤0 | **S** |
| C7 | Attack removal is demonstration-specific | Llama | `n_examples`=2 only | 40 rows, 5 attacks | prompt, 3 draws | demoproc 5/5 vs control 0.67/5, gap 0.1083 | arm-vs-arm 0.0417, 2.6× | same | count-matched non-demo mask (ratio 0.989) | **U** (one dose) |
| C8 | `query_prefill_only` is a measured null | Llama | d10 | 160 | domain | −0.0250, p=0.6875 | sign test, floor 0.0312 | attn knockout, query prefill rows | other scopes | **S** (negative) |

## 5. ⛔ Limitations that are properties of the BANK, not of the analysis

Two independent tests are **not constructible** here. Both need a new bank; neither is an analysis fix.

1. **Demonstration-specificity at the doses where the effect lives (R-25).** A count-matched non-demo
   attention control needs as many maskable non-demo positions as the demo block. The demo block grows
   **12 → 106 tokens**; the unprotected non-demo pool is near-constant at **~53** (the rest is the query
   span, which a control must not touch). `match_ratio` is **1.0 at n_examples=1, 0.0 at 4 and 8**.
   Rescoping to feasible rows is **forbidden** — demo length *is* the dose variable.
   **Fix: a bank with neutral filler context sized to the largest `n_examples`.**
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
| 3 | Causal rescue by activation patching? | **RUN, and REPLICATED on Qwen3 (R-35, R-36).** PR-13 Outcome C on ASR for Llama; Handing back clean demo-position activations at L14 recovers only **16.7%** of the ASR effect (within margin of knockout-only), but removes **69.2%** of the refusal rise (35→17 rows, >2× margin); the below-band L5 control moves refusal by **0.0000**. **The two effects have different substrates, shown causally on both models.** ⚠ On Qwen3 the same patch ALSO appears to restore the attack (0.0437 → 0.1062 vs clean 0.1313) — an **UNREGISTERED OBSERVATION**, explicitly not claimed per PR-14, needing its own pre-registration and replication. |
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
| C5 within-family bridge | `python src/boombness/binding_behaviour_bridge.py --bank <bank> --beh-baseline <j> --beh-arm <lab>=<j> --probe-baseline <run> --probe-arm <lab>=<run> --tag bridge` |
| all deliverable guards | `python src/boombness/check_all.py` |
| full suite | `python -m pytest tests/ doublespeak_causality/tests/ -q -p no:randomly` — **serial and exclusive** (C-2: concurrent runs corrupt committed artifacts) |

**Known repo hazards, carried here so they are not rediscovered:** `run_judge_cpu.sh` silently
discards `P2_*`; zsh does not glob unquoted parameters (build arg lists in Python); `--seed` is inert
at `--preset main`; `--export` truncates comma values; the full test suite mutates committed files and
must not run concurrently.
