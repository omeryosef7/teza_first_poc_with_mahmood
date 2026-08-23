# Boombness / `d_surface` sprint — complete self-contained summary, 2026-08-16 → 2026-08-23

**Project:** Tel Aviv University MSc research (Omer Yosef; advisor Mahmood Sharif; with Matan Ben-Tov).
Mechanistic interpretability of jailbreak / prompt-injection mechanisms.
**Repo:** `first_poc/teza_first_poc_with_mahmood`, branch `behavioral-causality-sprint`, HEAD `016f3c98`.
**Window:** first sprint commit `08227fb8` at 2026-08-16 18:04 → HEAD at 2026-08-23 16:07.

**What this document is.** A single self-contained account written for a reader with no prior
knowledge of the project — including an external LLM. It states what we set out to do, what we did,
what we did not do, where we won, and where we failed. Every number is quoted at the precision it is
stored at, with its producing artifact named.

**Verification status of this document.** Written 2026-08-23 by re-deriving every headline figure
from the committed JSON artifacts rather than from the project's own prose. 445 individual numeric
checks were run across both workstreams: **388 MATCH, 33 MISMATCH, 24 UNVERIFIABLE**, followed by 12
adversarial re-derivations of the disputed items (10 upheld the mismatch, 2 refuted it). The six
deliverable guards were executed live at HEAD and all six exit 0. §12 below lists every defect this
audit found in the project's own write-ups — those are *new*, not copied from the project's own
retraction registry.

---

## 1. What we set out to do

The plan is `docs/BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md` (21 sections, §0–§20, 1,208 lines, written
2026-08-16). Its §0 states the objective verbatim:

> We want to turn the discovered weakness into an explicit optimization objective for GCG/MAC-style
> optimization.
>
> In Doublespeak-style prompts, the model succeeds because benign surface tokens such as `carrot`
> acquire a hidden representation that is increasingly `bomb`-like. If we can measure this
> `boombness` signal, show that it predicts ASR, and show that removing it surgically reduces ASR
> without destroying prompt comprehension, then we can use it as an objective for GCG.

The intended end state was a combined attack objective of the form
`Boombness + Userness/CoTness − Refusalness`, in the style of *Prompt Injection as Role Confusion*
(arXiv 2506.12880, repo `matanbt/interp-jailbreak`, cloned to `external_repos/interp-jailbreak`).

**The three-step logical chain the plan depends on:**

1. **Measure** a scalar "Boombness" — how `bomb`-like the codeword's hidden representation is.
2. **Predict** — show that scalar correlates with attack success (ASR).
3. **Cause** — show that removing it surgically lowers ASR without destroying comprehension.

If all three hold, step 4 is to optimise a GCG suffix that maximises the axis.

**Four gates were pre-registered to test the chain:**

| gate | question |
|---|---|
| **G1** | Where does the codeword's meaning live — in the token, or in the demonstrations? |
| **G2** | Does Boombness predict attack success? |
| **G3** | Can the mechanism be removed surgically? |
| **G4** | Is it usable as an optimisation objective? |

**Plan §18 required a final label** from a four-way taxonomy: **A** strong positive · **B**
mechanistic but not causal · **C** refusal-only story · **D** negative. Plan §19 required eleven
named questions to be answered directly.

---

## 2. The one-paragraph answer

**The objective was not built, and should not be built.** The chain breaks at step 2 and inverts at
step 3. Boombness does **not** predict attack success (G2 is retracted after a sampling defect was
found). Steering the axis **suppresses** ASR at *both* signs, so there is no direction to optimise
toward (G4 is a directional null). Meanwhile the opposite manipulation — **removing** the direction —
**raises** attack success on external harmful prompts, which is the reverse of the plan's hypothesis.
That removal effect is real, causal, replicated on held-out external sets, and localized to a
mid-stack layer band — but it is an **order of magnitude smaller than the refusal channel**, is
**not shown to be specific to this direction rather than to how much variance any direction removes**,
and **fails to transfer to a second concept**. Plan §18 label: **C, amended** (refusal-only story,
with a second small channel the plain "C" label understates on Llama and which inverts on Qwen3).

---

## 3. Scale and resources — exact census

All figures re-derived from the filesystem and git at HEAD `016f3c98`.

| quantity | value |
|---|---|
| commits on `behavioral-causality-sprint` since 2026-08-16 | **719** (08-16: 53 · 08-17: 132 · 08-18: 105 · 08-19: 115 · 08-20: 60 · 08-21: 115 · 08-22: 86 · 08-23: 53) |
| distinct SLURM job ids (union of on-disk logs + commit messages) | **516**, range **760588–775064** (498 have logs; 223 named in commit messages; overlap 205) |
| log files / argsfiles / sbatch scripts | 1,202 / 421 / 13 |
| run directories under `outputs/boombness/` | **843** — judge 399, `score_behavior` 331, `surgical_knockout` 52, `extract_boombness` 20, `tokenization_audit` 18, probes 9, `aggressive_patching` 7, `refusalness` 5, section8 1, section9 1 |
| Python modules in `src/boombness/` | **91** (`.py`, excluding `__pycache__`) |
| committed JSON artifacts under `outputs/boombness/` | **131** tracked (124 top-level + 7 nested) of **4,135** on disk |
| committed JSON under `outputs/boombness_followup/` | **44** |

**Models — exactly two. There is no third model family in this sprint.**

* `meta-llama/Llama-3.1-8B-Instruct` — the default; `args.model=null` in 300 of 328 `score_behavior`
  configs and 15 of 20 extraction configs (~91% of all runs).
* `Qwen/Qwen3-14B` — explicit in 28 `score_behavior`, 5 extraction, 3 tokenization-audit runs;
  `enable-thinking false`, bfloat16.

(The `Phi-4-mini-reasoning` and Gemma directories visible in `git status` belong to the separate
`doublespeak_causality` sprint, not to this one.)

**Layers intervened on — 18 distinct, 304 interventional runs:**
L8 = 132 runs, L12 = 38, L10 = 29, L6 = 29, L18 = 26, L11 = 17, L20 = 5, L16 = 4, L13 = 4, L14 = 4,
L24 = 3, L28 = 3, L31 = 3, L4 = 2, L15 = 2, L25 = 1, L30 = 1, L29 = 1.

**Prompt banks — seven internal, three external.**

*Internal (all with `n_alignment_violations = 0`):*

| bank | rows | notes |
|---|---|---|
| `boombness_prompt_bank.jsonl` (carrot ↔ bomb, the primary 2×2) | **2,736** | 336 families; 6 domains × 456; splits dev 1,464 / heldout 1,272; seed 20260816; `bank_rows_sha16 = 4cd9157399aa1b3c` |
| `boombness_prompt_bank_button.jsonl` (button ↔ bomb) | 2,736 | the E6 codeword-swap vehicle |
| `boombness_prompt_bank_knife.jsonl` (carrot ↔ knife) | 2,736 | the E12 concept-swap vehicle |
| `boombness_prompt_bank_pinned_82bc1a3c_2352.jsonl` | 2,352 | the pinned early bank most §5–§10 work used |
| `boombness_prompt_bank_phase_d.jsonl` | 2,160 | 120 families, all behavioral, `n_examples=2` |
| `role_style_block.jsonl` | 720 | the G11 role-framing block |
| `boombness_prompt_bank_apple.jsonl` (apple ↔ bomb) | 2,736 | **VOID** — failed the mandatory §2.4 tokenization audit; untracked |

Primary-bank composition by condition: `natural_doublespeak` 1,008 · `benign_literal` 816 ·
`concept_in_benign_ctx` 384 · `direct_harmful` 384 · `benign_remap` 72 · `direct_codeword` 72.
By query kind: `behavioral` 1,152 · `semantic_one_word` 1,008 · `comprehension_usage` 288 ·
`semantic_forced_choice` 288.

*External — three, not four:*

| set | rows | clusters |
|---|---|---|
| `advbench_heldout_495.jsonl` | **495** | **16** domains; sizes 127/68/40/40/38/37/23/21/18/18/18/16/9/8/7/7 |
| `clearharm_179.jsonl` | **179** | **6** domains; `other_uncategorized` = **127** (71% in one bucket) |
| `benign_unrelated_40.jsonl` | 40 | 4 (science 14, practical 11, creative 8, math/code 7) |

69% of all behavioural scoring (225 of 328 runs) ran on AdvBench-495.

**Judge.** `strongreject_rubric` via the house `poc_stage3.strongreject_scoring` harness.
Candidate models `["openai/gpt-4o-mini", "openai/gpt-3.5-turbo"]`, tried in order with fallback.
⚠ **Which model actually answered any given row is not recorded anywhere and is not one model** —
`src/boombness/judge_boombness.py:465` says so explicitly. **Never attribute these scores to
GPT-4o-mini.** 399 judge run directories exist; primary threshold 0.5.

**Tokenization audits (plan §2.4, mandatory).** `n_failed = 0` on every bank shipped at HEAD
(2,352-row and 2,736-row banks, both models). Three audits are non-zero and all are of
superseded/abandoned artifacts, the important one being the apple bank at **36 failures of 2,748**.
Note for any codeword-swap claim: `carrot` is **two** tokens unspaced on both tokenizers
(Llama `[7063, 4744]` = `car`+`rot`), while `button` and `apple` are **one** — codeword swaps are
not token-count-matched to the primary bank.

---

## 4. The identification design — the one reusable methodological artifact

Everything rests on a **2×2 prompt design** that separates *surface identity* from *context*:

| | codeword `carrot` | concept `bomb` |
|---|---|---|
| **harmful context** | A: `natural_doublespeak` | C: `direct_harmful` |
| **benign context** | B: `benign_literal` | E: `concept_in_benign_ctx` |

Fitting on the cell means yields four directions, all from the same rows:

* **`d_surface`** — the surface-identity axis (the "Boombness" direction), the object of the sprint.
* **`d_context`** — the context axis, fitted by the same 2×2, near-orthogonal to `d_surface`.
* **`d_naive`** — the naive `carrot`-minus-`bomb` difference, without the 2×2 identification step.
* **`d_inter`** — the interaction term.

This design is what caught the sprint's own confounds *quantitatively* rather than rhetorically, and
it is the thing most worth carrying forward. **Its critical measured property:** `d_surface` is
essentially **PC1** of the cell-mean span (cos **0.9998–1.0000**), so it removes **0.81–0.88** of the
cell-mean spread while *any* direction inside the same rank-3 subspace removes **≤ 0.13**. That
6–11× dose gap is the caveat attached to nearly every causal claim below.

---

## 5. Day-by-day timeline

**08-16 (53 commits, sprint opens 18:04).** Prompt bank built and audited clean. Three
result-corrupting measurement bugs found and fixed within four hours (logit-lens token ids reading
`car` on the carrot side; a pre-patch readout via `hidden_states[L+1]`; wrong L31 coordinates). A
34-agent independent audit at tick 8 returned 25 findings, 9 result-corrupting → **retraction #1**.
G1 answered (meaning is in the demonstrations). G2 answered negative, then **reversed** the same
evening.

**08-17 (132 commits — the biggest day).** **Retraction #3** (attention edges cut into the wrong
destination token; job cancelled mid-run and rerun). **G4 returns NEGATIVE.** **Retraction #5**:
"Boombness beats refusalness 3.7×" was a token-position artifact and the ratio *inverts* to 0.80.
The §18 label moves C → B → C → B in one day on a phantom cell. Qwen3-14B replication launched.
**Retractions #6 and #7** (role-framing null inverted; a "four-draw control band" was n=1).
**19:35 — the pivot result:** removing Boombness *raises* ASR, inverting the sprint's guiding
hypothesis.

**08-18 (105 commits).** The external-datasets day. **ClearHarm-179 and AdvBench-heldout-495 added
in one commit at 17:22** (`external_bank.py`). First ClearHarm result at 18:13: arm D 0.101 → 0.542.
**R-8** ("the mechanism story is refuted while the empirical result survives"), **R-9/C-12** (metric
comparison across different populations), **R-12** (`control_seed` dropped on the composed path, so a
three-draw control band was one draw stated three times — re-creating retraction #7). An external
critique document is dated this day.

**08-19 (115 commits) — THE PIVOT DAY.** A cascade of six retractions in five hours:
**R-14** (every external-set arm judged against an **empty goal** — `external_bank` never emitted
`final_query_text`), **R-15**, **R-13**, **R-16**, **R-17** (Qwen3 cross-model claim withdrawn), and
**R-18 — G2 RETRACTED**: `analyze_g2` filtered on `condition` and not on `bank_block`, so the
published n=234 was 31% sibling families sharing demonstrations and 31% experimentally-manipulated
rows. **14:24: the formal pivot** — `external_md/BOOMBNESS_D_SURFACE_FOLLOWUP_PROGRESS.md` is
written, restating the goal as *"understand what `d_surface` actually represents"* and *"do not build
the GCG objective yet."* Its Phase A reproduction gate passes 90 minutes later.

**08-20 (60 commits) — the multi-session collision.** **RETRACTION F-3** (a "matched control" was a
14.8× dose mismatch). `benign_unrelated_40` added. Phase G opens. E6 codeword swap launched on the
apple bank. **At 17:37:17 three running Qwen3 jobs (769903, 769907, 769915) were cancelled by the
same account but by a different Claude session.** A peer session had independently found that the
apple bank fails the §2.4 gate two ways — 8 incidental collisions and **2,938 ungrammatical
"a apple" occurrences across 1,569 of 2,736 rows** against 671 grammatical "a bomb", the
ungrammaticality asymmetric across exactly the two contrasted cells. Consequences: the E6 apple
result was marked **pending re-test**, Phase H was re-based on a **button** bank, and the user
instructed *"shut it down for me i want only you to work on it."* One session then cancelled four of
another's jobs on a reason that was **false by seventeen seconds** (the peer had committed the proper
dtype fix 17 s after submitting, and SLURM reads the tree at run time) — recorded as **CORRECTION
C-1**. Also this day: **R-13** (Qwen3 arm-D replication uninterpretable — StrongReject scores answer
*style*), then a re-judge that **overturned R-13**; **DECISION GATE D: FAILED**.

**08-21 (115 commits) — the retraction cascade.** **R-23 + R-24 retract E12 in full.** **R-25**: the
in-subspace null was never dose-matched. **R-26**: `d_naive` beats `d_surface` at matched dose, so
the §14-D specificity conclusion falls. **R-27**: the entire dose-ladder inference chain, including a
geometric bound that was **algebraically false**. Also a reversal-of-a-reversal on the L31 control
within 100 minutes.

**08-22 (86 commits) — governance day.** An audit finds the phase board's decision-gate table
contradicting the report, with **four stale rows, two of them asserting the opposite of the report**.
Densification of the in-subspace null from 4 → 20 → 24 controls per depth
(jobs 774123–774138, 774260–774287, 774478–774493). An interim "L6 is REFUTED" headline is published
and then **retracted as a baseline-seed artifact of the author's own making**. **Review #13: the
standard error was wrong, and correcting it reverses the headline.**

**08-23 (53 commits, truncated at 16:07 = HEAD).** The 24-point grid completes and **the null
converges**. Reversals five through eight, including "the coherence gate flags refusal and has been
excluding good runs." Experiment 7 answered positively. **06:14 — BLOCKED: OpenAI credits
exhausted.** The rest of the day is consolidation: §19 sourcing driven to 13/13, guards wired to gate
commits, audits #14–#17, and a final commit whose message is *"the quoted analysis had never been
run."*

---

## 6. WHERE WE WON — the results that survive

Every number in this section was re-derived from the named artifact.

### 6.1 The headline causal result

**Projecting out `d_surface` raises attack success on held-out external harmful prompts.**
AdvBench-495, 16 domain clusters, Llama-3.1-8B-Instruct, baseline judge run
`abg_base_20260819_011714_1480836`. `d_surface` was fitted **entirely** on the carrot/bomb 2×2, so
this excludes the prompt-bank-artifact explanation — the most serious threat to every late finding.

| layer | Δ binary ASR (pooled) | net flips of 495 |
|---|---|---|
| **L8** | **+0.04242424242424243** | **21** |
| **L12** | **+0.03636363636363636** | **18** |
| L10 | +0.03232323232323232 | 16 |
| L6 | +0.01818181818181818 | 9 |

Continuous, domain-clustered, at L8: **+0.030519369707034255**, `p_cl` **0.008929531014546195**,
CI **[+0.00885299048927438, +0.052185748924794134]**, 16 domains
(`advbench_decomposition.json`). Binary domain-clustered: **+0.030580885455065754**.

⚠ **Four estimands travel under one headline** — binary-pooled / binary-clustered /
continuous-pooled / continuous-clustered — and the artifact's own `estimand_note` warns that its
CI and `p_cl` attach to `delta_cluster_mean`, not to the pooled delta.

### 6.2 The in-subspace null — the control that matters

The right null is not a random 4096-d direction (near-orthogonal to everything, and far too weak —
this is what **R-23** retracted). It is **other directions inside the same rank-3 cell-mean
subspace**. `insubspace_null_full24.json`, **24 controls per layer**, 7.5° grid, `grid_complete: true`,
`n_common: 495`, `population_matched: true` at all four layers:

| layer | arm Δ | max control Δ | arm/ceiling | control ceiling in prompts |
|---|---|---|---|---|
| L6 | 0.01818181818181818 | 0.010101010101010102 | **1.80×** | 5 of 495 |
| L8 | 0.04242424242424243 | 0.01818181818181818 | **2.33×** | 9 |
| L10 | 0.03232323232323232 | **0.0** | undefined (all controls ≤ 0) | 0 |
| L12 | 0.03636363636363636 | 0.010101010101010102 | **3.60×** | 5 |

`arm_exceeds_all_controls: true` at all four layers; `rank_p_one_sided = 0.04` everywhere, which is
the design's floor (1/25).

**The null converged.** Refining L6 12→24, L8 12→24, L12 8→24 and L10 **4→24** left the control
ceiling **bit-identical** in every case. That is the empirical answer to the standing objection that
this is "a sample, not a bound" — although 24 directions in a 2-d complement remains a sample.

### 6.3 Layer localization

`advbench_layer_profile.json` — **11 arms and 11 matched norm-preserving random-projection controls**
(complete except L15).

* Band: **~L6–L14**, scan-statistic window `{L6, L8, L10, L12, L13, L14}`, permutation
  **p = 0.0109** under layer-label exchangeability.
* Core, uncorrected per-layer: **L12 p_cl 0.005616851753647907**, **L8 0.008929531014546195**,
  **L10 0.018975646328411498**; L6 marginal at 0.05669575145748033.
* **L16 is exactly 0.0** (`degenerate: true`) — and it is *not* a failed intervention: the same
  intervention still changes **29.5%** of generations there while changing compliance on none.
  L18/L24/L28 are ≈ 0.0037 / 0.0005 / 0.0037, all n.s.
* **All eleven matched controls are inert:** range **−0.0065810589586711874 (c24) to
  +0.0047149937229104 (c10)**, no p_cl below 0.20.
* Baseline refusal 0.9313131313131313 → 0.8888888888888888 (L8) / 0.898989898989899 (L10) /
  0.8949494949494949 (L12), and back to 0.9313131313131313 at L16.

⚠ **No single layer survives Holm** over the 10-layer family. What licenses the band is the *shape*
test, not any per-layer p.

### 6.4 The gain is real refusal→compliance conversion, not judge noise

Two independent lines, both verified:

* **Length.** The 21 L8 flips go from a median of **67 characters** at baseline to **2,474** in the
  arm (range 2,067–2,674, all at the 512-token cap), against a median of 67 across all 495 baseline
  rows. These are refusal→full-answer conversions.
* **Topicality** (`advbench_topicality_L8/L12.json`) — the test that killed arm F (R-20), finally
  applied to the headline. Fraction of the request's distinctive content words appearing,
  word-bounded, in the completion:

| set | n | mean | median | zero overlap |
|---|---|---|---|---|
| L12 refusal→compliance flips | 18 | **0.784** | 0.800 | **0%** |
| L8 refusal→compliance flips | 21 | **0.823** | 1.000 | **0%** |
| every row scored ≥ 0.5 in the L12 arm | 50 | 0.737 | 0.800 | 0% |
| baseline non-compliant rows *(floor)* | 200 | **0.115** | **0.000** | **81%** |

Not one flipped completion has zero overlap. ⚠ This shows subject matter, not correctness or
usefulness. ⚠ The n=50 and n=200 rows are both from the L12 file; the L8 analogues are n=53 mean
0.7966 and mean 0.1244 / 80% zero.

### 6.5 The refusal channel — the sprint's large, robust result

This is the finding that actually holds up at scale, and it is about **refusal**, not about Boombness.
AdvBench-495, binary ASR:

| arm | pooled | clustered | continuous pooled | continuous clustered | net flips |
|---|---|---|---|---|---|
| **C** — remove refusal direction | **+0.2061** | +0.2024 | +0.1967 | +0.1895 | 102 |
| **D** — remove refusal **and** `d_surface` | **+0.2869** | +0.2710 | +0.2722 | +0.2544 | **142** (143 gross, one back-flip) |

Both survive every multiplicity family tried (Holm ≤ 0.002) with inert controls; AdvBench goes
0.065 → **0.352**. ⚠ Their p-values (**0.0001220703125**) sit exactly at the exact-test's attainable
floor with 14 of 16 informative domains, so they are sign tests and **cannot discriminate D from C**.

On ClearHarm-179 (`clearharm_decomposition_regoal.json`): baseline **0.10614525139664804** → arm D
**0.5139664804469274**, `p_cl` **0.020009428282769054**.

**Super-additivity** (`superadditivity_signflip.json`): +0.03333333333333333 continuous /
+0.03838383838383838 binary, 13 / 10 informative clusters, exact cluster sign-flip
**p = 0.007568359375 / 0.0078125**, random-triple control inert (+0.0066, p = 0.25).
⚠ **But the contrast against that control is p = 0.055** — narrowly short. "Significant with an
inert control" is weaker than "significantly greater than its control", and the report correctly
withdrew the stronger phrasing.

### 6.6 G1 — where the meaning lives (established)

`g1_wholeanswer_sow.json`, whole-answer readout, 24 families in 6 domains, domain-clustered paired
bootstrap:

| transplant arm | % of span | CI |
|---|---|---|
| **`demos_only` at L18** | **+0.6887043836439078** | [+0.5127769879731333, +0.9741707744164648] |
| `query_only` at L18 | **−0.5700186200834122** (wrong direction) | [−1.0276334040857735, −0.4010533864705643] |
| `all` (whole prompt) at L18 | +0.13292718438116716 (null) | [−0.16716144629998553, +0.3388987190017967] |

Ceiling-free absolute Δ log-odds, which needs no denominator: `demos_only` **+5.659
[+3.305, +8.314]**, `query_only` **−4.684 [−5.358, −4.043]**, G=6. Self-swap control moves
0.06486034393310547 / 8.217080619186163 = **0.79%** of span.

**The meaning of the codeword lives in the demonstration block, not in the codeword token.** This
is the sprint's cleanest positive result and it survived the readout defect that voided other work
(the old instrument gave +68.1% against the corrected +68.9%).

### 6.7 G3 — the retrieval is attention-carried and massively redundant (established)

`g3_wholeanswer_block24.json`: cutting **all** demonstration-block attention edges across all layers
gives Δ **−13.436758967737356** against a text-deletion ceiling of **−17.878933541476727** =
**75.15%** of the ceiling, at **81,706.67** edges cut. Sparse knockout does not work: top-k
**+0.019611094146966934** (sem 0.016518567912713653), bottom-k −0.0028310430546601615, random
+0.0008226409554481506. **The redundancy is in the edge count, not in a small set of heads.**
Domain-clustered interval widths are ×1.6525 and ×1.1846 wider than the family-level ones for the
two arms that carry the claim.

### 6.8 Cross-model: Qwen3-14B uses a *different* channel

Corrected `qwen3_l20_regoal.json`, **960 paired ids**, all four arms re-judged against real goals:

| condition | n | baseline | `D20` | matched control | Δ |
|---|---|---|---|---|---|
| `natural_doublespeak` | 420 | 0.17142857142857143 | **0.5190476190476191** | 0.18571428571428572 | **+0.33333333333333337** |
| `benign_literal` | 324 | 0.0 | **0.2222222222222222** | 0.009259259259259259 | +0.21296296296296297 |

`C20` (refusal removal alone) = 0.16666666666666666 — **on Qwen3 refusal removal does nothing.**
At L11, `d_surface` alone gives **+0.38095238095238093**, `p_cl` **0.00030870570185738953**, against a
hard in-subspace control that is null (−0.011904761904761904, p 0.6007, 6/6 leave-one-domain-out
folds n.s.).

**So the two models are mirror images.** On the same external set (ClearHarm-179, re-judged,
`clearharm_decomposition_regoal.json`, pooled) Llama's refusalness arm gives **+0.24022346368715083**
against `d_surface`'s **+0.08310055865921788** — refusal dominates. On Qwen3 the reverse: `d_surface`
moves ASR 0.134 → 0.279 while refusalness at L20 does nothing. ⚠ The Qwen3 ClearHarm magnitude is
**pooled-only** and does not survive clustering (cluster-mean +0.04161655137035764, p_cl 0.18103).
⚠ `D20` also moves *benign-by-construction* prompts to 0.2222 — a real specificity problem on Qwen3.

### 6.9 Experiment 7 — the bidirectional half (positive signal, not yet established)

`outputs/boombness_followup/exp7_dsurface_add.json`, 9 arms, 495 prompts each, one judging session
(judge job 774835, analysis job 774974):

| arm | dose | Δ StrongReject | p_cl |
|---|---|---|---|
| `d_surface:add` | 0.0625 gap | −0.018475569995389875 | 0.06930052411789904 |
| `d_surface:add` | 0.125 | −0.02243033844768703 | 0.09110906277802185 |
| `d_surface:add` | 0.25 | −0.029271824898759884 | 0.07168713003221186 |
| `d_surface:add` | 0.50 | **−0.03571908582067251** | **0.025414693523694763** |
| `random:add` (matched) | 0.50 | ⚠ **+0.05292440142841176** | 0.010454593005811514 |
| `random:add` | 0.75 | +0.15069934735752577 | 0.0006623868085147007 |
| refusalness add | 1/8, 1/4 | −0.013403480211925124, −0.023073929267517612 | 0.2167, 0.0700 |
| **interaction dS50 − rnd50** | | **−0.08864348724908426** | **0.007144584975029605** |

**Removing the axis raises ASR; adding it lowers ASR, with a perfectly monotone four-dose response**
(exact-order probability 1/4! = 0.042, an estimator-free statistic). That is what a causal axis
should do, and neither half establishes it alone.

⚠ Three caveats, all backed by the artifact: the interaction **fails Holm at m=9** (0.05715667980023684);
**59.70%** of the interaction is the *control moving up*, not the arm suppressing; and the matched
control is a **single draw**.

### 6.10 The process layer — a genuine deliverable

15 self-audit scripts in three tiers, all present at HEAD:

* **Six gating guards**, bundled by `check_all.py` with one exit code and deliberately no `--skip`:
  `retraction_sweep`, `canonical_figures`, `verify_report_numbers`, `markdown_structure_check`,
  `pvalue_hygiene_check`, `plan_coverage_check`. **All six exit 0 at HEAD — verified by live run
  during this audit.**
* **Five data-side scanners:** `shard_citation_check` (29 sharded runs, 0 findings),
  `answer_regenerability_check` (14 answers, 6 flagged), `unwritten_findings_check` (89 checked,
  0 silent), `readout_gate_check` (18 non-reportable runs, 9 dependent artifacts, 6 live),
  `empty_goal_leakage_check` (15 tainted runs, 9 dependent artifacts, 3 live).
* **Four index/labelling builders** that deliberately return no verdict: `unanalysed_inventory`,
  `unanalysed_triage` (333 judge runs done, 9 uncited, 8 `COULD_CHANGE`), `population_index`
  (62 artifacts), `label_artifacts`.
* `scripts/guarded_commit.sh` — refuses to commit if any guard fails. ⚠ It gates only commits made
  *through the wrapper*; deliberately not a git hook, because the repo was shared with concurrent
  sessions, so plain `git commit` bypasses it.

Each guard was written against a specific defect that had already occurred — see §11.

---

## 7. WHERE WE FAILED — the results that died

### 7.1 G2 is retracted: Boombness does not predict attack success

The single most expensive loss. `analyze_g2` filtered rows on `condition` and **not** on
`bank_block`, so the published sample was heterogeneous and nobody looked at its composition.

| sample | n | within-domain ρ | permutation p |
|---|---|---|---|
| published (contaminated) | 234 | **+0.26178047909981317** | 0.0004997501249375312 |
| clean, four blocks | 90 | **−0.05180076147796621** | 0.657671164417791 |
| `core2x2` only | 60 | −0.08319340452385668 | 0.5722138930534733 |
| powered re-run, disjoint demonstrations | **108** | **−0.06601851932290928** | **0.49325337331334335** |

The published n=234 was **31% sibling families sharing demonstrations** and **31%
experimentally-manipulated readability rows**. The correlation is recoverable **only** by putting the
contaminated rows back. ⚠ n=90/108 cannot exclude a small effect — this is a null, not a proof of
absence.

### 7.2 G4 is a directional null: there is nothing to optimise toward

`steering_analysis.json`, n_common = 270 `natural_doublespeak` prompts, Welch t against a 4-draw
between-seed variance. **Both signs of `d_surface` suppress ASR.** Only `+0.25` clears the random
control band (p = 0.0014) — and it does so **by triggering refusal in 90.1% of generations**.
The `−0.25` arm does not clear (p = 0.070) and refuses 0%. ⚠ `steer_a025` is the only arm with
coherence attrition (202 of 270 kept), so its ASR sits on a partly different set from its controls.

**This is why plan §12 was never built.** It is the sprint's most consequential negative result.

### 7.3 E12 is retracted in full: `d_surface` names an estimator, not a concept

Both halves of the concept-transfer test failed **pre-committed** controls.

* **Behavioural (R-23).** The knife-fitted direction gives +0.0182 (9 flips) at L8 — but an
  in-subspace direction **orthogonal** to `d_surface` (cos **0.0000**) reproduces that *exactly*.
  Knife z = **1.34** against that null; it does not clear. (Bomb z = 3.23.) The published "half
  strength" ratio was also computed **across two different layers** (L8 vs L12).
* **Representational (R-24).** Holding the **concept** fixed and swapping only the **codeword**
  (`button` → `bomb`) moves `d_surface` **further** (cos **0.5539**) than holding the codeword fixed
  and swapping the concept (cos **0.6117**), against a within-concept split ceiling of **0.995** and
  with identical family sets.

**Conclusion, verbatim from the report:** *"`d_surface`, as estimated at the codeword token, is at
least as much a function of which token carries the codeword as of what that codeword means. The
mechanism is demonstrated for `carrot ↔ bomb` and for that pairing only."*

### 7.4 Direction specificity is NOT established (R-25, R-26, R-27)

Three retractions in one day dismantled the specificity argument:

* **R-25** — the in-subspace null was never dose-matched. The arm removes 0.81–0.88 of the cell-mean
  spread; every control removes ≤ 0.13 (`dose_gap_arm_over_max_control` = 10.96 / 7.36 / 6.17 / 6.83
  at L6/L8/L10/L12, `dose_confounded: true` at all four). Within the L6 null,
  Spearman ρ(dose, Δ) = **0.961**.
* **R-26** — the "specificity control" (`d_context` moves ASR by ~zero) is confounded by dose.
  `d_context` removes only 0.13, which sits *inside the range where every in-subspace direction is
  inert regardless of meaning*. And at **matched dose**, `d_naive` — the direction you get *without*
  the 2×2 identification step — produces a **38% larger** effect: **+0.0586 (29 flips)** at dose
  0.7919 / cos 0.9613, against a ladder rung matched on both dose (0.7969) and cosine (0.9749) that
  gives **+0.0444 (22 flips)**. So the identification step does not merely buy nothing — it moves you
  **off the stronger direction**.
* **R-27** — the whole dose-ladder inference chain, six defects, including a geometric bound that
  was **algebraically false**. What survives is only: *the dose-response is monotone and saturating,
  and nothing beyond that is established.* The ladder itself is a valid measurement:

| dose | 0.8402 | 0.7969 | 0.6835 | 0.5224 | 0.3456 | 0.1881 | 0.0810 | 0.0457 |
|---|---|---|---|---|---|---|---|---|
| Δ ASR | +0.0424 | +0.0444 | +0.0424 | +0.0404 | +0.0263 | +0.0222 | +0.0101 | +0.0020 |

From dose 0.52 to 0.84 the effect barely moves — most of it is bought by the first half of the dose.

**And the design cannot be fixed by a better control.** With `d_surface` at cos ≈ 1.0 with PC1 of the
cell-mean span, any direction reaching high dose is forced to be nearly collinear with it. Separating
"this direction" from "how much variance it removes" needs a **different bank**, whose cell-mean
spectrum is not dominated by a single component — not more compute.

### 7.5 The follow-up line's final multiplicity verdict: no depth is established

This is the harshest surviving result and it must travel with §6.2. From
`outputs/boombness_followup/angle24_specificity_FULL.json`, the complete 24-control paired grid:

| family | L12 | L10 | L8 | L6 |
|---|---|---|---|---|
| raw worst-case p | 0.01830547920057915 | 0.024384640580560647 | 0.10353024782718524 | 0.6782717805522958 |
| **Holm, m=4** | **0.0732219168023166** | **0.0732219168023166** | 0.20706049565437049 | 0.6782717805522958 |
| Holm, m=11 (layer selection) | 0.20136027120637065 | 0.24384640580560646 | 0.9317722304446672 | 1.0 |

**`rejects_at_0.05` is empty in both families.** The same design produced three different Holm
verdicts depending on which baseline/session was used — 1 depth rejects
(`control_recheck_subspace.json`), 4 depths reject (`control_recheck_sessionmatched.json`: 0.0136 /
0.0276 / 0.0347 / 0.0347), and **0 depths reject** (`angle24_specificity_FULL.json`). **The last is
the final one.** The widely-quoted `0.0136 / 0.0276 / 0.0347 / 0.0347` tail is single-draw
(one control per depth) and must never be cited without this table.

### 7.6 Decision Gates C and D of the follow-up line both FAILED

* **Gate C — FAILED.** No probe in the suite is usable as a Boombness metric.
  "Maximise probe margin" is dead as an objective.
* **Gate D — FAILED on requirement 4.** A clean Fig-9-style bank *does* show Boombness predicting
  ASR — and this one survives every guard the design was built for, unlike G2. But **`d_naive` and
  `d_context` predict just as well**, so the signal belongs to the *subspace*, not to `d_surface`.
  Additionally, roughly two thirds of the pooled correlation is the design's own manipulation.

### 7.7 The negative results, enumerated (report §8b — 16 of them)

| # | question | answer |
|---|---|---|
| **N1** | Does a pure Boombness objective increase attack success? | **No.** Steering suppresses ASR at both signs. Plan §12.1 is dead. |
| **N2** | Does the Boombness↔ASR correlation replicate on a second model? | **No.** ρ ≈ +0.307 at L12 on Llama does not carry to Qwen3-14B. |
| **N3** | Does the *final* `carrot` become more `bomb`-like than earlier ones? | **No — less.** And the sign is set by query *format*, not by meaning. |
| **N4** | Do the three Boombness metrics (probe / direction / logit-lens) agree? | **No.** They disagree in **sign** about ASR at L12; `common_all_three` covers only **72 of 270** rows. |
| **N5** | Is the meaning stored in the codeword token? | **No.** Transplanting the query codeword moves the readout the wrong way. This negative is what makes G1 positive. |
| **N6** | Does the projection result replicate on Qwen3 *on the bank*? | **No** — it raises judged harmfulness on benign prompts too. Off-bank the picture differs again. |
| **N7** | Is the effect harm-general rather than doublespeak-specific? | **Not established, and these data cannot answer it.** Only 1 of 6 condition cells is distinguishable from zero. |
| **N8** | Is the ClearHarm joint arm super-additive? | **Not established.** +0.0922, clustered CI [−0.147, +0.133]; 127 of 179 rows in one cluster. |
| **N9** | Is `d_surface` "concept-ness" off-bank? | **Not licensed.** The 2×2 named a contrast that does not exist in a codeword-free prompt. |
| **N10** | Do the probe splits leak across families? | **No** — the external critique's leakage finding is refuted against a real K=20 null (max excess 0.021 vs a 0.05 tolerance). |
| **N11** | Is `n_examples` a confound for the correlation? | **No.** It predicts ASR (ρ=+0.206) but is uncorrelated with Boombness (ρ=−0.034); partial ρ retains 99.9%. |
| **N12** | Can plan §4.1's designed variance be analysed? | **No** — 192 rows, largest comparison 12 behavioural rows per level, `position` is 6 vs 6. Documented and excluded. |
| **N13** | Does the causal effect replicate on Qwen3? | **Not established; neither external set can answer it.** Qwen3 complies with **0.8% of AdvBench (4/495)** vs 13.4% of ClearHarm. An intervention cannot be measured against a floor. |
| **N14** | Are two external harmful sets interchangeable? | **No, and the choice can decide the answer.** Llama baselines 0.106 / 0.065; Qwen3 0.134 / 0.008. |
| **N15** | (G2 restated) | ⛔ Retracted — see §7.1. |
| **N16** | Is `n_examples` a confound for G2? | **Superseded** — the question does not arise until G2 is re-established. |

Two of these (N10, N11) are negatives **against the external critique**, not against the sprint.

---

## 8. WHAT WE DID NOT DO

### Never built, deliberately
* **`gcg_objectives.py` and `run_boombness_gcg.py`** — plan §12's actual deliverable. Not an
  oversight: G4's negative is the documented reason (N1). Plan §17's Phase 8 was never entered,
  correctly, because the plan gated it on earlier gates passing.

### Never built, not flagged as missing in the report
* `role_confusion_variants.py`, `plotting.py`, `utils.py` (functional equivalents exist:
  `role_probes.py`, the section8/section9 plot dirs, `common.py`).
* `prompt_level_correlation.py` / `example_count_sweep.py` — the work exists as
  `summarize_section9.py` / `summarize_section8.py`, which read committed artifacts rather than
  re-running the sweeps. Same outputs, different provenance path.

### Never fitted at all
* **No Userness/CoTness probe was ever fitted** (plan §11 / §17 Phase 7 step 3). `role_style` remains
  a categorical proxy. The planned combined objective `Boombness + Userness/CoTness − Refusalness`
  therefore never had two of its three terms.

### Generated but never analysed
* **Plan §4.1's designed variance** (`strength`, `consistency`, `example_position`) — 192 rows in
  three dedicated `bank_block`s, analysed by nothing, and shown in N12 to be unable to support
  inference. Worse: **72 of those rows were inside G2's headline n=234** (R-18). The report calls
  "generated-confounded-unexamined" the worst of the three possible states.

### Scope never reached
* **A second concept pair as a *positive* result.** E12 ran and was retracted in full. Three
  alternative banks (apple, button, knife) were built and audited at 2,736 rows each; the apple one
  was voided by its own audit. Every surviving claim in the report is `carrot ↔ bomb`.
* **A third model family.** Everything is Llama-3.1-8B-Instruct and Qwen3-14B. No quantized variant
  was tested (plan §14 suggested one).
* **A behavioural-prompt knockout.** G1/G3 are computed on `semantic_one_word` prompts while
  G2/G4's ASR claims are on `behavioral` ones. Each is internally consistent; joining them into one
  causal story is the manipulated-≠-measured pattern one level up. This is the single cleanest
  next experiment.

### Plan coverage lint
18 of the plan's 21 sections are cited in the report. **§1** (repo clone), **§16** (directory
structure), **§17** (execution order) are not — all three are in the lint's non-research allowlist,
and §1/§16's work was in fact done; the gap is documentation, not execution.

---

## 9. Open items — blocked, not abandoned

**⛔ BLOCKED 2026-08-23 06:14: OpenAI credits exhausted.** The `bnd2` judging batch failed —
the log `outputs/boombness/logs/bnd2judge_775064.out` contains **443** occurrences of
"You have no credits remaining". **Zero of six runs completed.** Nothing is lost: all pending
**generations are on disk at 495 rows each and need no GPU rework**, and everything concluded above
was judged before the cutoff. The partial judge directories (453–473 of 495 rows) were deleted rather
than left to be found by a `newest()`-style lookup; no partial dir remains on disk.

**Exactly three things are pending credits:**

1. **The experiment-7 control band.** Three already-generated `random:add` draws at the matched 0.5
   gap: `e7rnd01` (seed 20260901, job 774975), `e7rnd02` (20260902, 774976), `e7rnd03` (20260903,
   774977), 495 rows each. Until these are judged, the −0.0886 interaction rests on **one** control
   draw. **This is the single most important pending item** — it decides whether experiment 7 stands.
2. **The dose-matched arms.** `dd12a008` (`d_surface:project_out:12-12:0.08`, removal fraction
   **0.126020**, *inside* the controls' ≤0.13 band) and `dd12a006` (`:0.06`, removal **0.095500**,
   below it) — jobs 774865 / 774866, 495 rows each. This is the test of whether direction matters
   independently of dose, i.e. the answer to the `DOSE_CAVEAT` that governs §7.4. It is
   pre-registered as underpowered, so a point estimate and CI are to be reported, not a verdict.
   *Note the correction that made these doses right:* `project_out` scales the *component*, so
   removed variance goes as **1 − (1−α)²**, ≈ 2α for small α — the first four launched doses
   (α 0.10–0.30) were all **above** the control ceiling and would have been called "dose-matched".
   Measured table at L12 (total squared norm **62.791954**): α 1.00 → 0.820443, 0.30 → 0.418426,
   0.20 → 0.295359, 0.15 → 0.227673, 0.10 → 0.155884, **0.08 → 0.126020**, 0.06 → 0.095500.
3. A matching baseline judge run for that session.

**Also open:** re-judging the in-subspace control arms with a session-matched baseline.

---

## 10. The final answer to the plan's own questions

**Plan §18 outcome label: C, amended.**

| option | verdict | why |
|---|---|---|
| **A** strong positive | **No** | Adding Boombness does not increase attack behaviour; steering suppresses ASR at both signs; no GCG objective was built or should be. |
| **B** mechanistic but not causal | **No** | B requires that interventions *neither* affect ASR *nor* destroy comprehension. **Both clauses fail**: removal raises external-set ASR, and comprehension is not destroyed — it **improves**, by **+0.27947553790484864**, CI [+0.175, +0.384], n=288 over 6 domains, while the double-random control is flat at **−0.004092160819305314**. ⚠ The published p=0.00099 is **below the 6-domain attainable floor of 2/2⁶ = 0.03125**, so it is a bootstrap p, not clustered evidence; the exact cluster sign-flip test gives arm p=0.03125 (at floor) vs control p=0.875. |
| **C** refusal-only story | **Closest** | On Llama refusal is the dominant channel: +0.190 against `d_surface`'s +0.031 on AdvBench. |
| **D** negative | **No** | `d_surface` is not "unstable, non-predictive or confounded after alignment fixes" — removing it causally raises attack success on 495 external prompts. What it does *not* do is **predict**, which is why the label is C-amended and not A. |

**The amendment**, stated at its correct strength: the second channel is *small*, its "distinctness"
rests on **2 prompts** (19 of `d_surface`'s 21 L8 flips are also refusal's), its "interaction" is
**cannot-determine** (arm D's flip set is a near-superset; pure dose predicts 39 of its 40 novel
flips), and on Qwen3-14B **the picture inverts entirely**.

**Plan §19's eleven questions are all answered in report §19, and as of 2026-08-23 all 13 answer
blocks name a committed artifact** — a state reached only on the final day, after the sourcing check
found five answers quoting figures that named nothing, and one (Q5's `core2x2` −0.0832 / p 0.572)
that had been quoted for six days while existing in **no artifact at all**. It now reproduces to the
digit from `g2_analysis_cwpos_CORE2X2.json`.

---

## 11. How we worked — and the failure modes worth carrying forward

The sprint's most transferable output may be its error taxonomy. Eight recurring shapes, each of
which bit the project more than once:

* **FM1 — The dead guard.** A guard whose condition can never be true. **Seven enumerated**, six of
  which matched on an *incidental property* — a filename, a tag prefix, an mtime, a line number, a
  JSON key's presence — rather than on identity. One was written **while fixing dead guards**; one
  was the author's own, on the last day, and was **green by construction** and committed in that
  state. **Standing countermeasure: every guard ships with a test that fails the pre-fix code.**
* **FM2 — The one-of-two-paths miss.** A fix applied to the single-spec path and dropped on the
  composed path. Three occurrences, most recently R-12.
* **FM3 — The unfalsifiable-by-inspection artifact.** A fake control band looks *better* than a real
  one; an ASR table judged against an empty goal still returns a plausible *ordering*.
  **Check the input, not the output, for any artifact whose value is what you are trying to
  establish.**
* **FM4 — Mismatched footing.** Two probes read at different tokens; two increments with different
  degrees of freedom. Produced R-5 (the "3.7×"), and then produced R-13 *inside the paragraph
  announcing R-5's retraction*.
* **FM4b — The heterogeneous row set.** R-18, the most expensive instance. **A count is not a
  description of a sample.**
* **FM5 — The instrument that cannot represent the answer.** The `semantic_logodds` readout scored
  two single tokens at a position holding a median **5.6e-06** of next-token mass, and was biased
  4-ids-to-1 toward the concept because the model capitalises and `Carrot` is multi-token.
* **FM6 — The silent failure.** A dispatch with no `else`; a `make_goal` returning a bare string so
  an empty goal recorded `judge_status: "ok"` (R-14).
* **FM7 — Robustness checks that test the wrong thing.** The 3.7× survived nested cross-validation
  and leave-one-domain-out and was still an artifact — both resample **rows**, and the defect was in
  **where** the arms were measured.
* **FM8 — The deliverable drifting from the evidence.** **Standing bar: every number in the report
  must be regenerable by a committed script from a committed artifact. If the script and the
  artifact cannot both be named, the number does not go in.**

**Registry census.** **R-1 … R-27** retractions (22 individually tabled as R-6…R-27, plus a pointer
row for R-1…R-5, plus a third `#1…#9` numbering series in the progress log). **Four retractions were
themselves later reversed or narrowed**: R-7 (discharged), R-16 (reversed), R-26 (declared an
*over*-retraction), and the L6 sub-clause inside R-25.

**Statistical discipline adopted mid-sprint, and worth keeping:**
* With *k* informative clusters, the attainable two-sided cluster p-floor is **2/2ᵏ** — **0.031 at 6
  domains**, 3.1e-5 at 16. A p below its design's floor is bootstrap or parametric, **not clustered
  evidence**.
* **Quote the delta; quote the p as a range.** Across four independent judge passes on
  byte-identical generations, L12's p spans **0.0020–0.0078** (4×) and L8's **0.0039–0.0273** (7×),
  while the deltas barely move (L12 +0.0343…+0.0384, L8 +0.0404…+0.0444). Under Holm over the
  12-arm family, L12 survives in **3 of 4** passes and L8 in **1 of 4** — "survives Holm" is itself
  pass-dependent.
* The right noise scale is **end-to-end replicate noise**, not judge drift. Judge drift on the
  AdvBench baseline is **0.0020202020202020193** — one prompt in 495 — over 13 complete passes.
  End-to-end replicate noise over the same-config pairs is **median 1 prompt, max 7**.

---

## 12. Known defects in the project's own write-ups (found by this audit, 2026-08-23)

These are **new** — they are not in the project's own retraction registry. Listed so that a reader
of the primary documents is not misled. None changes a scientific conclusion; all are quotation,
denominator, or provenance errors.

| # | where | what is wrong | correct value |
|---|---|---|---|
| 1 | §0a replicate-noise table, both deliverables | "17 same-config pairs on the 495 bank (19 incl. **two** larger-bank pairs)"; "15 of 17 ≤ 2"; "1 of 17 exceeds L6's margin" | `replicate_noise.json` has 19 pairs = **18** at n=495 + **one** at n=960. So **16 of 18** ≤ 2 and **1 of 18** exceeds. Counts right, denominators wrong; the stale "17" is repeated in `null_ceiling_session_check.py:144` and `orth_control_arms.py:16`. Conclusion unaffected. |
| 2 | §14-L gate row (report line 710) and line 1953 | "matched controls at **five** depths … (−0.0066 to +0.0007)" | There are **11** matched controls at 11 depths, range **−0.0066 to +0.0047**. The five-depth subset {c4,c8,c12,c18,c24} does span −0.0066 to +0.0007, so the sentence is true of its own stated scope but stale; the report's own line 1971 says "all eleven". |
| 3 | §8 heading | "**C-1 … C-14** corrections" | The C-registry table has **nine** rows: C-1, C-5, C-6, C-8, C-9, C-11, C-12, C-13, C-14. C-2/C-3/C-4 exist only as unhyphenated `C2/C3/C4` in prose; **C-7 and C-10 appear nowhere in the report at all**. `retraction_sweep.py` misses this because it only checks *cited* ids. |
| 4 | report line 502 and `check_all.py`'s own docstring | "**Five** guards, one exit code" | **Six**. `plan_coverage_check` was the sixth. |
| 5 | §1b implementation scale | "36 modules"; "244 committed run **directories**"; "32 test files"; "584 passing tests" | **91** tracked `.py`; **244 tracked FILES** across only **13** tracked directories; **37** files in `tests/` of which 20 mention boombness; the 584 figure has no committed artifact. |
| 6 | `plan_coverage_check.py` | summary line says "all 21 plan sections are cited" while its own table prints **NO** for §1/§16/§17; docstring says "20 numbered sections" and "3,089 lines" | 21 sections; report is **3,610** lines. |
| 7 | §0a super-additivity | "Holm over the session's tests takes it to **0.083**" | Arithmetically self-consistent (0.007568359375 × 11, rank 5 of m=15) but **no artifact computes an m=15 family**; `multiplicity_families.json` covers only 6 tests and excludes super-additivity. Same for the companion "0.047" for L12. |
| 8 | report lines 759 and 2256 | Qwen3 "remove `d_surface` alone: +0.526 plain / +0.464 topical / +0.440 [+0.357, +0.521]", and the benign rows | These figures exist in **no file** under `outputs/boombness/`. The clean L11 analogue is 0.5310 / 0.4762 — near, not equal. |
| 9 | report line 172 | Qwen3 G2: "+0.364 pooled, but **+0.015 after dropping one domain**" | ρ_pooled = 0.3638023338654771 verifies, and 3/6 per-cluster ρ are positive — but `qwen3_g2_analysis.json` has **no leave-one-domain-out field**; the +0.015 is unsourced. |
| 10 | §7c / gate row §10.4-D | ClearHarm "0.106 → 0.514, p_cl = 0.020" cited to `clearharm_decomposition.json` | That file is the **superseded pre-R-14** run (0.1006 → 0.5419) and contains **no p_cl at all**. The numbers come from `clearharm_decomposition_regoal.json`. |
| 11 | E6 identity | Stated **three different ways in one report**: §9b table "button ↔ bomb DONE", §9b body "apple ↔ bomb is the recommendation", §1b "a second concept pair — not delivered" | Three banks were built and audited (apple 2,736 / button 2,736 / knife 2,736). The apple bank **failed** its audit and E6 ran on **button ↔ bomb**. Any prose calling apple/bomb the E6 vehicle describes a cancelled run. |
| 12 | various | "four external datasets" | **Three**: `external_bank.py`'s `SOURCES` has exactly 3 entries (ClearHarm, AdvBench-heldout, benign_unrelated_40). The apple/button banks are generated in-repo, not external. |
| 13 | §14-D | cos(`d_context`, `d_surface`) @L8 = 0.188 | Two artifacts disagree: `direction_cosines.json` = **0.18844406306743622**, `dose_vs_effect.json` = **0.20662231743335724** (different fit/split). A real inconsistency, not rounding. |
| 14 | §0a headline | "+0.0305 domain-clustered, p = 0.0089" flagged by `how_to_read_the_p_values.json` as not clustered evidence | **The flag is wrong and the report already knows it** (§0b lines 410–415 retracts exactly this example): AdvBench clusters on 16 domains, floor 3.1e-5, 8 informative clusters at L8 giving floor 0.0078 — 0.0089 is above both. The stale JSON is the defect, not the prose. |
| 15 | §0a, on the concurrent line | "the concurrent line's ceiling growth +0.0118 → +0.0172 … is **unreconciled and unreproducible from any committed script or artifact**" | **The reproducibility charge is false.** Both endpoints are stored at full precision: **0.011750854472893946** in `angle_band_L6_full.json` and **0.017171060798676835** in `angle_band24_new.json` (ratio 1.4613 = +46%); the L8 analogue reproduces too (+24.0%). **The substantive charge is correct**: on a common baseline, **0 of 20** controls reach the arm at L6 (arm 0.01919344133036891 vs max 0.017171060798676835 = 89.5%), and the follow-up had already retracted the exceedance itself as a seed artifact. |
| 16 | `angle24_specificity_FULL.json` | `caveats.session` still ships the **superseded** drift figure 0.0040 | Corrected drift is 0.0020202…; the correction is markdown-only, so a downstream script consuming that artifact gets the retracted number. |
| 17 | follow-up log | "402 × RateLimitError" | The on-disk log has **443** occurrences of "You have no credits remaining" and **886** of "RateLimitError"; the literal string "402" appears **0** times. (It was probably meant as the HTTP status.) |
| 18 | guard layer | `answer_sourcing_check.json` (n_flagged = 7) is still committed beside `answer_regenerability_check.json` (n_flagged = 6), and `answer_sourcing_check.py` **no longer exists** | Two artifacts for one check — exactly the "stale file that reads as current" failure the layer's own `git_commit_safe()` docstring calls "the worst failure mode available". |

**Also worth knowing:** the report's §9b status header ("six of eleven are DONE") introduces a table
with **14** rows (E1–E14), 8 marked DONE; and `label_artifacts.py`'s "126/126 scripts carry a
docstring" matches no directory count at HEAD (91 in `src/boombness`, 58 in `scripts`).

---

## 13. Reconciling the two workstreams

Two concurrent lines ran on one branch and one SLURM account, and they reported conflicting things
about the same experiment. **The conflict is now resolved and it was never a contradiction:**

* The **main line** (`insubspace_null_full24.json`, baseline `abg_base`, **pooled binary
  ASR-flip** metric) shows the control ceiling **bit-identical** between the coarse and 24-point
  grids at all four depths → *"the null converged."*
* The **follow-up line** (`angle_band_*`, baselines `abrep_base`/`a24_base`, **domain-clustered mean
  StrongReject**) shows the ceiling rising **+46%** at L6 and **+24%** at L8 → *"denser grids find
  stronger controls."*

**Different metric, different baselines, different judging sessions. Both statements are true of
their own artifact family, and the two lines never measured the same quantity.** On the substantive
question — *does any control reach the arm?* — every seed-matched artifact from both lines says
**no**: 0 of 20 and 0 of 24 at all four depths. The one reported exceedance came from pairing an arm
judged at seed 20260821 against controls judged at seed 20260816, a ~0.0023 baseline offset larger
than all three "exceedances" combined, and the follow-up line retracted it itself in its Review #12.

**What both lines agree on at the end:** the arm beats every in-subspace control at every depth
tested, and **no depth survives Holm** once the layer-selection family is accounted for (§7.5).

---

## 14. What a successor should take from this

1. **The 2×2 identification design is the reusable artifact.** It separates surface identity from
   context, and it caught the sprint's confounds quantitatively.
2. **Do not build the GCG objective on this axis.** G4 is a directional null on two independent
   lines (the sign test, and the refusal-route split). If an objective is wanted, target the
   **demonstration-retrieval pathway** that G1/G3 localized, not the codeword's position on
   `d_surface`.
3. **The next bank must not be PC1-dominated.** The dose/identity entanglement (§7.4) is a property
   of *this* bank's cell-mean spectrum, not of the compute budget. A bank whose cell-mean spread has
   two or three comparable components would let dose and direction be separated for the first time.
4. **Close the manipulated-≠-measured gap.** G1/G3 are on `semantic_one_word` prompts; G2/G4's ASR
   claims are on `behavioral` ones. A behavioural-prompt knockout would join them into one causal
   story that is currently two.
5. **Report baseline compliance beside every external-set ASR.** N14 is the cheapest lesson here:
   Qwen3 complies with 0.8% of AdvBench and 13.4% of ClearHarm, and choosing either set alone yields
   a confident, opposite, wrong cross-model conclusion.
6. **Judge the pending five runs first.** They are generated, on disk, at 495 rows, and they decide
   whether experiment 7 and the dose-matched comparison stand (§9).

---

## 15. Reproducing this

Python: `/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`
(scipy 1.17.1, sklearn 1.9.0, torch 2.7.1+cu126, transformers 5.12.1 — **the login shell has none of
these**). All analysis is CPU-only and committed; every gate-bearing number comes from
`src/boombness/analyze_*.py` reading a committed artifact.

```bash
# verify the deliverables are internally consistent (all six must exit 0)
python src/boombness/check_all.py

# the five data-side scanners
python src/boombness/shard_citation_check.py       --out /tmp/a.json
python src/boombness/answer_regenerability_check.py --out /tmp/b.json
python src/boombness/unwritten_findings_check.py    --out /tmp/c.json
python src/boombness/readout_gate_check.py          --out /tmp/d.json
python src/boombness/empty_goal_leakage_check.py    --out /tmp/e.json
```

Full reproduction commands for the GPU pipeline (bank → extraction at **both** readout positions →
behaviour → judge → refusalness at both positions → G1/G3/G4 → analysis) are in report §"Exact
commands to reproduce the main runs" (line 3523 of
`reports/boombness_objective_sprint_report.md`). Note the judge refuses to start without
`OPENAI_API_KEY`, by design.

### Primary source documents

| document | lines | status |
|---|---|---|
| `reports/boombness_objective_sprint_report.md` | 3,610 | **CURRENT.** §0a is the one-screen state; §0b the supporting detail. |
| `reports/boombness_objective_sprint_short_update.md` | 865 | **CURRENT**, revision 7 (2026-08-23). |
| `external_md/BOOMBNESS_D_SURFACE_FOLLOWUP_PROGRESS.md` | 9,793 | **CURRENT** — the follow-up line's live log. |
| `docs/BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md` | 1,208 | The original plan (2026-08-16). |
| `docs/BOOMBNESS_CONTINUATION_LOG.md` | 10,324 | Live execution log. |
| `docs/BOOMBNESS_SPRINT_PROGRESS.md` | 6,054 | Phase board. |
| `reports/BOOMBNESS_SPRINT_HANDOVER_2026-08-16_TO_08-19.md` | 6,636 | ⛔ **SUPERSEDED** — predates R-23…R-27 and C-11…C-14. Kept as a dated record only. |

---

*Compiled 2026-08-23 at HEAD `016f3c98`. Every figure above was re-derived from committed JSON
artifacts rather than from project prose; §12 lists every place the two disagreed.*
