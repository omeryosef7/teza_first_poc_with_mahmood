# Boombness Objective Sprint — Progress Log

**Plan:** [`docs/BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md`](BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md)
**Branch:** `behavioral-causality-sprint`
**Started:** 2026-08-16
**Owner:** Omer Yosef (TAU MSc, adv. Mahmood Sharif) · executed by Claude Code

This file is the single place to track sprint progress. Every loop tick appends here.
Status vocabulary: `TODO` · `IN PROGRESS` · `DONE` · `BLOCKED` · `NEGATIVE (documented)` · `SKIPPED (justified)`

---

## Phase status board

| Phase | Plan § | Description | Status | Evidence |
|---|---|---|---|---|
| P1.1 | §1 | Clone `interp-jailbreak` to `external_repos/`, strip `.git` | DONE | `external_repos/interp-jailbreak/` @ upstream `89620cf` (2025-06-20) |
| P1.2 | §1 | `notes/interp_jailbreak_best_practices.md` | DONE | `notes/interp_jailbreak_best_practices.md` (252 lines, 10 sections) + `notes/boombness_reuse_inventory.md` + 6 scout reports |
| P1.3 | §3 | Aligned prompt generator `src/boombness/prompt_families.py` | DONE | `src/boombness/prompt_families.py` — 2×2 design, 6 domains, 8 axes |
| P1.4 | §3.1 | Generate 50 prompts + manual review | DONE | 1464 rows, 180 families, 0 alignment violations; `data/boombness_prompts/manual_review_50.md` reviewed |
| P1.5 | §2.4 | Tokenization audit | DONE | `tokenization_audit.py`: 1464 ok / 0 bad / 0 ambiguous; 8472/8472 occurrences single-token; 540 families, 0 token-alignment violations |
| P1.6 | §3 | Iterate generator until alignment + tokenization OK | DONE | two defects found and fixed (substring-vs-whole-word filter; quote/sentence-initial tokenization), bank regenerated clean |
| P2.1 | §5.1 | Hidden-state replacement, smoke | DONE | `aggressive_patching.py`; transplant verified by an exact self-swap no-op |
| P2.2 | §5.2 | Additive bomb-direction sweep, smoke | DONE | additive sweep in **gap units** (α=1 = one diff-of-means); dose bug fixed twice |
| P2.3 | §5.3 | Metrics + comprehension controls validated | DONE | forward-only readouts validated; comprehension answer pair fixed to single tokens |
| P2.4 | §5 | Pilot 30–50 prompts | DONE | pilot `pilot_20260816_210506_1142800`, 8 families, 2368 rows |
| P2.5 | §5.4 | `decision_gate.md` | DONE | G1 recorded with propagated intervals via `analyze_g1_g3.py` |
| P3.1 | §6.1 | Logit-lens Boombness | DONE | `signals.logit_lens` + `logit_lens_boombness_batch`; ids validated by `readout_id_pair` |
| P3.2 | §6.2 | Direction Boombness | DONE | `signals.estimate_directions` — the 2×2 estimator (`d_surface`/`d_context`/`d_inter`/`d_naive`) |
| P3.3 | §6.3 | Simple probe | **DONE — uninformative by design, documented** | d1/d2 label is the SURFACE WORD, so AUROC=1.000 at every layer including block 0. Trivial; must not be quoted as Boombness decodability. `probes/headline_20260816_200516` |
| P3.4 | §6.3 | Hard-negative / held-out-condition probe | **DONE — same defect** | d3's C-vs-E test set is also a carrot-vs-bomb contrast, and d4 shares the surface label, so both read 1.000 for the same trivial reason. The retracted d4 convergence claim stays retracted. |
| P3.5 | §6.4 | Metric comparison | **DONE — superseded by surface-matched regimes** | Added `d5_surface_matched_codeword` (A vs C) and `d6_surface_matched_concept` (B vs E): AUROC ~0.98 at all layers, shuffled at chance, and NOT explained by length/position (both alone = 0.47). Shows context reaches the codeword token; does not show the content is bombness. `probes/surfmatch_20260817_103543` |
| P4.1 | §7.1 | Token-level Boombness per occurrence × layer | DONE | 8472 occurrence rows, per-occurrence × per-layer, run `full_20260816_185942_1008673` |
| P4.2 | §7.1 | Occurrence × layer heatmaps | DONE | `analysis/plots/occurrence_x_layer_*.png` for all four 2×2 cells |
| P4.3 | §7.1 | Later-carrot-more-bomb-like test | RETRACTED | "two-humped / null carry band" invalidated by the tick-8 audit |
| P4.4 | §8 | Example-count sweep | **DONE (08-17)** | Full n_examples×layer dose-response written up with cluster-robust t: L4–L12 positive and strictly monotone in demo count (L8 +0.0138→+0.0449, 4/4 steps); L16–L24 negative with dose-dependent magnitude saturating at k=8 (L20 −0.051); **L31 FLAT across a 16× dose change** (+0.044 to +0.050, t=+5.9..+10.2) — one demonstration achieves the whole output-layer effect. `reanalyze_d_surface_cos.json` |
| P5.1 | §4 | ~600-prompt bank | DONE | 1752-row bank (`bank_content_sha16` 59ad8c8c44f7c3fa) |
| P5.2 | §9 | Generations + evaluation | DONE | `base_20260816_203355_3985444` (660 gens) + judge, null_frac 0.0000 |
| P5.3 | §9 | Prompt-level Boombness | DONE | `analyze_g2.py`, 100% coverage, committed and reproducible |
| P5.4 | §9 | Correlation / regression | DONE | G2 + §9 Q6/Q7 mediation vs refusalness |
| P5.5 | §9 | Figure-9-style plot | **DROPPED, deliberately** | The figure would have plotted the ASR-vs-Boombness relation that RETRACTION #5 shows is not the operative one. Producing a polished figure of a superseded framing is worse than producing none. If a figure is wanted it should be the predictor×position 2×2 (`outputs/boombness/position_2x2.json`). |
| P6.1 | §10.1 | Attention edge knockout | DONE | `surgical_knockout.py` with `--dst`, `--demo-scope`, and 2 dynamic-range controls |
| P6.2 | §10.2 | Head knockout | **NOT RUN — superseded by the B4a result** | Per-head knockout asks which heads carry the retrieval. The edge-matched experiment showed removing **6.25%** of demo edges does nothing however distributed, so any per-head cut (16 edges, ~0.03%) is guaranteed to read zero — as every localized arm already did. The experiment is not informative at this redundancy level; running it would only add another null to misread. |
| P6.3 | §10.3 | Direction knockout | DONE | direction knockout covered by the additive/ablate arms |
| P6.4 | §10.4 | Combined Boombness/refusal | **DONE (08-17), and it decided the §18 label** | Answered by the matched-position analysis rather than a separate experiment. On the same 234 prompts with both probes at `codeword_last`: refusalness alone R²=0.176 (5 layers jointly 0.257), `d_surface|L12|proj` alone 0.141; adding Boombness to refusalness buys **+0.012 to +0.076**, while adding refusalness to Boombness buys **+0.144**. Boombness is close to redundant given refusalness at matched position, which is the direct evidence for outcome C. |
| P6.5 | §10 | Comprehension controls | DONE | comprehension readout live (`comprehension_usage`, log-odds) |
| P6.6 | §10 | Causal vs destructive separation | DONE | `coherence_gate.py` separates causal from destructive |
| P7.1 | §11 | Role-style variants | DONE | role_style axis in the bank (6 styles) |
| P7.2 | §11 | Role framing → Boombness | **DONE (08-17), powered** | Superseded by P7.4's powered run: `role → Boombness(L12)` F=0.175 **p=0.972**, style-mean spread 3.6% of within-style sd — a tight null, not an underpowered one. |
| P7.3 | §11 | Userness/CoTness probes (if feasible) | **NOT FITTED — disclosed as a proxy** | `role_probes.py` ports the Role-Confusion machinery but no probe was fitted on this model, so §11 uses `role_style` as a CATEGORICAL PROXY throughout and every table says so. Not claimed as a measured role signal. |
| P7.4 | §11 | Boombness + role predicts ASR | **DONE (08-17), powered** | 72 extract + 36 ASR rows per style. `role → Boombness(L12)` F=0.175 **p=0.972** — a tight null, style-mean spread is 3.6% of within-style sd. `role → ASR` F=1.94 p=0.087, largest pair 0.035 vs 0.233 (MW p=0.007 uncorrected, ~0.105 Bonferroni) = suggestive, NOT established. Answer is (c)-leaning, not the (b) I predicted at tick 35. |
| P8.1 | §12.1 | Boombness GCG objective | **CLOSED — gate not met** | The steering test (α∈{0.10,0.25,1,2}) is the prerequisite and it returned a directional null: both signs suppress ASR, only +0.25 clears a 4-draw random-control band (p=0.0014) and it does so by triggering refusal. No directional causal support ⇒ no objective. Documented negative. |
| P8.2 | §12.2 | Boombness − refusal objective | **CLOSED — gate not met** | G4 found no directional causal support for `d_surface`; an objective maximizing this projection is not justified. Documented negative, deliberately not run. |
| P8.3 | §12.5 | Baseline / refusal-only comparison | **CLOSED — gate not met** | conditional on P8.2. |
| P8.4 | §12.5 | Universality + held-out transfer | **CLOSED — gate not met** | conditional on P8.2. |
| P8.5 | §15 | Final reports | **DONE (rev 4)** | `reports/boombness_objective_sprint_short_update.md` revision 4 — supersedes rev 3, which reported a conclusion built on a phantom cell. Carries 5 retractions, 5 corrections, the freedom-matched position 2×2, and the §18=B label. |

---

## Decision gates

| Gate | Question | Verdict | Date |
|---|---|---|---|
| G1 (§5.4) | Can we force `carrot` to be `bomb`-like, and does it change behavior? | **PASS on DIRECTION; magnitude is one arm of ~130 and must be named.** The lever is the DEMONSTRATION block, not the codeword: `transplant|demos_only|L18` on the harm-context pair moves the semantic readout **+84% of span, paired-bootstrap CI [+57%,+105%]** (n=8 families from only **2 domains**); the query-codeword transplant moves it the WRONG way (−0.58 to −0.81). ⚠ **Arm-selection exposure, disclosed:** in the same context pair `transplant|demos_only|ALL` moves the readout strongly the wrong way (−0.76, CI [−1.49,−0.21]), so "transplanting the demonstrations" is not uniformly +84% — the single-layer L18 window is. ⛔ The previously quoted "+23% to +135%" was a CHIMERA (L8's lower bound welded to L18's upper) and is withdrawn. | 2026-08-17 |
| G2 (§9) | Does prompt-level Boombness predict ASR? | **YES, with corrected inference: `d_surface|L12|proj`, rho=+0.307, norm-partial +0.302, n=234, 100% coverage, 6/6 domains positive (2 essentially null). p = 5.0e-04 within-domain permutation / 1.2e-03 CR1-clustered — NOT the i.i.d. 1.7e-06.** ⛔ Two earlier verdicts superseded: ~~L8 proj rho=+0.342, p=8e-08~~ (C1: L8 is the most norm-contaminated layer, norm-free +0.172 fails Holm) and ~~the original negative~~ (R2: predictor read off the wrong prompt). | 2026-08-17 |
| G3 (§10) | Can Boombness be removed without destroying comprehension? | **RESOLVED, and the depth reading is RETRACTED (B4a). Cutting query→demo-block attention at all 32 layers recovers 84% (CI [62%,110%]) of the deletion ceiling; at 2 layers 0.07% (CI [−6.7%,+8.2%]). But the edge-count-matched arm shows layer spread is NOT the operative variable: 3,552 edges over 32 layers moves the readout +0.09, the same nothing as 3,552 edges at 2 layers (−0.01). The redundancy is in the EDGE SET — removing 6.25% of demo edges does nothing however distributed, removing 100% recovers 84%. The converse arm is impossible: a layer holds only ~3,648 edges, so any cut >7.3k edges must span layers. Identification one-sided by construction.** | 2026-08-17 |
| G4 (§12) | Is Boombness a usable GCG objective? | **NO — a documented NEGATIVE.** Both signs of `d_surface` at a coherent dose suppress ASR (paired Δ −0.114 and −0.074), so mean ASR does not follow the sign and no objective is licensed. Against a **4-draw** random-control band (mean −0.0366, between-draw sd 0.0049): **+0.25 clears it** (t=−3.23, Welch df=235, p=0.0014) and **−0.25 does NOT** (p=0.070) — so the earlier "2–3× the controls" wording is retracted as sign-blind. The two signs suppress by different routes: +0.25 via refusal (90.1% of its suppressed prompts), −0.25 via generic degradation (0.0%, matching controls). ⚠ +0.25's coherence verdict was computed on 202/270 rows (68 short generations skipped). | 2026-08-17 |
| FINAL (§18) | A strong-positive / B mechanistic-not-causal / C refusal-only / D negative | **B — mechanistic but not causal (SETTLED 08-17 on rebuilt real cells).** Freedom-matched 2×2: ratio Boombness/refusalness = 1.54 [0.64,3.60] @last and 0.75 [0.33,1.13] @codeword_last — **both CIs straddle 1**, so neither probe dominates and C is not supported. POSITION dominates for both (2.0× and 4.2×), which is the surviving positive finding: the ASR-predictive state is localized at the codeword token. The 3.7× retraction stands — it was the most favourable of the four cross-position pairings. §12's objective unsupported (G4 directional null). | 2026-08-17 |

---

## Bug / integrity audit log

Every 4h an independent agent audits code + outputs for result-affecting bugs. Findings land here.

| Date | Auditor | Finding | Severity | Fix | Rerun needed? |
|---|---|---|---|---|---|
| 2026-08-16 | self-review workflow, `review:directions` lens | **`all_first_ids` put the generic token `car` on the codeword side of every logit-lens score.** `word_token_ids` took the FIRST id of each surface variant. On Llama-3.1-8B `" carrot"`→`[' carrot']` but `"carrot"`→`['car','rot']`, `"Carrot"`→`['Car','rot']`, `" Carrot"`→`[' Car','rot']` — so **3 of carrot's 4 "first ids" are car-the-vehicle**, one of the most frequent tokens in the vocabulary, while all 4 of bomb's variants genuinely spell bomb. | **result-corrupting** | Added `signals.readout_ids` / `readout_id_pair`. Default `primary` mode = the single leading-space whole-word token per side (`' bomb'` vs `' carrot'`) — exactly symmetric, and exactly the token that appears in our prompts. Multi-token variants are recorded under `rejected_first_ids` instead of scored. Raises if the leading-space form is not single-token. | **YES — cancelled job 760596 mid-run at 600/1464 rows and resubmitted as 760598.** Direction metrics (`d_*`) were unaffected (they use no token ids); the `ll\|*` logit-lens columns were. |
| 2026-08-16 | §5 smoke (job 760661) | **Readouts at the patched layer were PRE-patch.** `out.hidden_states[L+1]` is filled by the framework's own capture, registered before ours, so at the very layer being intervened on it reported the value the patch was about to overwrite. Measured: patching window `L8` left the L8 boombness readout bit-identical to baseline (−0.2294) while a window containing layers *below* 8 moved it (+0.1477) — the readout only ever saw upstream effects and reported "no effect at the intervened layer" **by construction**. | **result-corrupting** | New `BlockCapture` registers our own forward hooks on the decoder blocks *after* the patch contexts, so they run later and read the block's true output. Wired into all 5 readout call sites. | **YES — smoke 760661 discarded, resubmitted as 760681.** No full run had been done, so nothing published was affected. |
| 2026-08-16 | §5 smoke (job 760661) | **The L31 readout in `aggressive_patching` was in the wrong coordinates.** `forward_hidden` was fixed for the last-layer norm tie, but `readout()` read `out.hidden_states` directly, so its L31 projection mixed post-norm activations against directions fitted on raw block outputs. | **result-corrupting** | Same `BlockCapture` fix — reading the block's own output is raw by construction. | Same rerun. |
| 2026-08-16 | §5 score smoke (job 760663) | **All 8 behavioural generations died with `KeyError: 'text'`.** `ds_common.generate` returns `{"completion", "n_new_tokens", "stop_reason", …}`; my code read `g["text"]`, and the fallback `g["text"] if isinstance(g, dict) else str(g)` checked the *type* but assumed the *key*. | crash (caught) | Use the documented `completion` key, raise with the actual key list if absent, and also persist `n_new_tokens` / `stop_reason` / `gen_truncated`, which plan §5.3 asks for anyway. | Yes — smoke resubmitted as 760684. **Nothing was silently lost:** the `FailureLedger` reported 8/8 failures with the reason, which is precisely the §2.2 contract working. Had this been a bare `except: pass`, it would have produced an empty `gens.jsonl` and read as **ASR = 0**. |
| 2026-08-16 | tick-8 independent audit (34 agents) | **25 confirmed findings, 9 result-corrupting.** Four invalidate the tick-7 headline (unreported query-kind restriction; mid-band "null" is a sign-flipping n_examples cancellation; probe convergence computed on a superseded run; L31 delta confounded with bank regeneration). Others: pseudo-replication (n=60 not 30, domain ICC≈0.53); no multiplicity correction over 32 layers; null asserted without an interval; `--intervene add` reintroduced the unit-vector dosing bug; probe table omitted L31; `metadata.json` records the git commit at FINISH not start; no consumer checks `DONE.json`; plan §2.1 model/tokenizer/dataset revisions missing. | **result-corrupting** | Full retraction written below; `reanalyze_corrected.py` added (per-query-kind + pooled, layer×n_examples surface, domain-clustered SEs, Holm, intervals for nulls); dosing recurrence fixed in `score_behavior`. | **YES — tick-7 claims retracted; probes re-run against the headline run; analysis redone.** |
| 2026-08-16 | §5 pilot (job 760722) | **The pilot was launched on a query kind for which a position-matched transplant is undefined.** `semantic_forced_choice` names both words, so donor cell B's query reads `bomb…carrot…bomb` while recipient cell C's reads `carrot…carrot…bomb` — the target occurrence positions do not correspond. All 16 families were rejected by the live position assertion (`pair_occurrence_positions_differ`), producing 0 rows. | crash (caught) | The assertion behaved correctly; the launch should not have been possible. `aggressive_patching` now **refuses** any query kind with `occurrence_analysis_safe=False` up front, naming the safe alternatives. Pilot re-run on `semantic_one_word` (job 760731). | Yes — 0 rows had been produced, so nothing was invalidated. |
| 2026-08-16 | `dominance.py` self-test (job 760719) | Device mismatch: `v` stayed on cuda while the per-head projection was moved to cpu, so the `D_dir` einsum raised. | crash (caught) | All single-destination arithmetic is now done on CPU float32 explicitly. | Yes — resubmitted as 760730. |
| 2026-08-16 | §10 positive control (job 760741) — **CORRECTED, see the row below: the primitive DOES fire.** ~~`AttentionKnockout` appears NOT TO FIRE under transformers 5.12.~~ Original reasoning kept for the record: The positive-control arm blocked **every** pre-query key in **every** head at two layers — 7392 edges, leaving the final token attending only to itself — and the semantic readout moved by **−0.086 log-odds**. That is physically impossible if the mask edit reached the attention computation. `AttentionKnockout` raises when the mask is not 4-D and it did *not* raise, so a 4-D mask was present and was edited; the question is whether transformers 5.x still *uses* that per-layer kwarg under its pluggable attention interface. | **result-corrupting** | `diagnose_knockout.py` measures it unambiguously: capture attention weights with and without a total knockout. Job 760757. | **All §10 knockout results are void pending this.** Scope may extend beyond this sprint: any prior work in this repo that used `AttentionKnockout` under this transformers version is affected. |
| 2026-08-16 | `diagnose_knockout.py` (job 760757) | **CORRECTION to the row above — `AttentionKnockout` DOES fire.** A total mask-out at L8 drove the last token's attention mass on prior keys from **0.945 → 0.000** (self-attention 0.055 → 1.000), `max\|Δ attention weight\| = 0.997`, `max\|Δ final logit\| = 1.157`. My inference that "0.086 log-odds is impossible" was wrong: one layer's attention at one position changes final logits by only ~1.16, and the semantic **log-odds ratio** can move far less than that because both terms shift together. | — (my error, not a code defect) | No fix needed to the primitive. The §10 null may therefore be a **genuine** null. One difference remains untested: the diagnostic used a single all-head knockout, while `surgical_knockout` **stacks one context manager per head**. Job 760762 tests whether those compose identically. | **RESOLVED (job 760762): stacked per-head composition is bit-identical to the all-head form (max|Δ|=0.0), so the machinery is verified end to end and the §10 null is genuine.** No prior repo result is implicated — that warning is withdrawn. |
| 2026-08-17 | tick-16 audit finding, verified 2026-08-17 | **FATAL to all of §10: the knockout cut edges into the WRONG DESTINATION.** Edges were blocked into `dst = the final codeword occurrence` (token ~104) while the readout is the next-token distribution at the **last token** (~113) — **9 tokens away**, measured on every prompt in the run. Blocking attention arriving at a position the readout does not directly depend on can only act indirectly, which is why every arm read ≈0 and why only `no_demo_text` (which deletes the text) moved anything. | **result-corrupting** | `--dst {readout,codeword,both}` added, defaulting to the position actually measured. Also fixed: the positive control was blocking the destination's own **self-edge**, making the whole softmax row `-inf` and the result a degenerate uniform row rather than "attend only to yourself". | **YES — the G3 resolution recorded one tick earlier is RETRACTED. Job 760814 cancelled mid-run (same flaw); rerunning as 760816 with `--dst both --demo-scope block`.** |
| 2026-08-17 | tick-16 audit | **The `random` and `orthogonal` controls were the same draw.** `pair_common.orthogonal_random` internally calls `norm_matched_random` with the SAME seed and projects out the component along `d`; in 4096-D that component is ~1/√4096 ≈ 0.016, so the projection changes ~0.02% of the vector. Reporting "random and orthogonal both fail" was **one observation stated twice**, not two independent controls. The tell was there: the two arms agreed to 3 decimals (−0.168 vs −0.167; −3.945 vs −3.948). | **minor (over-claimed control strength)** | `orthogonal_control_direction` now offsets the seed, so the two are independent draws. | Controls should be re-run; the *direction* of the G1 control conclusion is unaffected (both were far from the `d_surface` arm), only its strength as evidence. |
| 2026-08-17 | tick-16 audit | **The `dominance.py` invariant was an algebraic TAUTOLOGY.** `D_attn := <Y, ΣY>/‖ΣY‖²` sums to 1 for **any** `Y` whatsoever — including one built with a wrong GQA head map or wrong `o_proj` slicing. The "selftest OK — the GQA head mapping and o_proj slicing are correct" claim verified **nothing**. | **result-corrupting (a verification that verified nothing)** | Replaced with a real check: capture the module's actual `o_proj` output at `dst` via a hook and require the reconstructed `ΣY` to match it to 1e-3 relative. Job 760862 (after the print was also corrected). | **RESOLVED: reconstruction relative error 3.9e-07 at L8 and 3.7e-07 at L18** — `sum(Y)` reproduces the module's own `o_proj` output, so the GQA head map and slicing are genuinely correct and the §10 edge ranking rests on a verified decomposition. |
| 2026-08-16 | the fix's own guard | **The comprehension forced choice was unanswerable.** `readout_ids` raised on the answer word `"codeword"`: it tokenizes to `[' cod','ew','ord']` (3 tokens), so the single-next-token readout was measuring the mass on `' cod'`, not on the intended answer. | **result-corrupting** | Answer vocabulary changed to `literal` / `coded`, both single tokens (`' literal'`=24016, `' coded'`=47773), so the two options are symmetric. Query template reworded to match. | Yes — bank regenerated, tokenization audit re-run clean (1464 ok / 0 bad / 0 ambiguous, 540 families / 0 violations); no prior comprehension results existed to invalidate. |

---

## Tick log

### 2026-08-16 — Tick 0 (sprint start)
- Read plan, project memory (SLURM rules, cyber-safeguard subagent rule, SDPA rule, position-index bug class).
- Confirmed environment: SLURM up, L40S nodes `n-801..805`, `t-806`; no jobs of ours running; conda `base` + `poc_stage2`.
- **P1.1 DONE:** cloned `https://github.com/matanbt/interp-jailbreak.git` into `external_repos/`, recorded upstream commit `89620cfe0f78a0741e739889ef2e5cd47fe96dc1` (2025-06-20 "Update hijacking analysis"), removed `.git`.
  - Verified byte-identical to the pre-existing root-level `interp-jailbreak/` copy (only extra file there is the paper PDF) → the repo's existing copy was already up to date.
- Launched scouting fan-out (6 agents) over `interp-jailbreak` + our `doublespeak_causality` code to maximize reuse before writing anything new.
- Environment: torch 2.7.1+cu126 / transformers 5.12.1 / sklearn 1.9 / scipy / pandas / matplotlib in conda env
  `poc_stage2` (NOT `base` — base has no torch). **No `transformer_lens`**, no `seaborn`, no `statsmodels`
  → we use plain HF forward hooks (which our repo already does) rather than the paper's TransformerLens fork.

#### F1 (§3 alignment) — the SEMANTIC family is already perfectly aligned; the *benign* arm is not

Measured on `data/pair_benchmark/pair_carrot_bomb.json` (800 semantic prompts, carrot↔bomb):

| pair | mean string similarity | exact word-swap identical? |
|---|---|---|
| `DIRECT_CONCEPT` vs `DOUBLESPEAK` | **0.937** | **YES** — `direct.replace("bomb","carrot") == doublespeak` |
| `NEUTRAL_CODEWORD` vs `DOUBLESPEAK` | **0.326** | no |

So Direct↔Doublespeak is a *pure lexical swap over identical sentences* — better aligned than the plan
assumed. But the **benign-literal arm is a different story entirely** (farmer / market / smoothie /
cake vs exploded / defused / detonation / blast).

**Consequence, and it is the central methodological problem of this sprint:** the plan's §6.2 direction
`d_bombness = mean(h_bomb in direct) − mean(h_carrot in benign-literal)` is computed across two arms
that differ in *both* the surface token *and* the entire semantic domain. Such a direction is
`bombness + explosive-context-ness`, and any "Boombness predicts ASR" result using it is confounded.

**Design response (supersedes plan §6.2's simple difference):** use a 2×2 factorial that separates the
two effects, keeping the *final query sentence byte-identical except for the target word* in every cell:

| | demo block = benign domain | demo block = harm domain |
|---|---|---|
| **surface = carrot** | `A` benign literal | `C` natural doublespeak |
| **surface = bomb** | `E` bomb-in-benign-context (hard negative, plan §6.3) | `B` direct harmful |

`d_bombness` = main effect of surface word **within matched context** (`(B−C) and (E−A)` averaged),
`d_context` = main effect of domain (`(C−A) and (B−E)`). The plan's naive direction is `B−A`, which is
the *sum* of the two effects. This is a real improvement over the plan and is worth reporting to
Matan/Mahmood on its own.

#### F2 (§3 alignment) — the BEHAVIORAL triplet is misaligned by construction

`doublespeak_causality/ds_common.py:814-816` (`build_conditions`):

```python
direct      = f"{prefix} {harmful_instruction} {suffix}"                 # NO demo block
neutral     = f"{prefix} {substituted_query} {suffix}"                   # NO demo block
doublespeak = f"{demos}\n\n{prefix} {substituted_query} {suffix}"        # demo block present
```

Measured over all 900 behavioral rows of the carrot↔bomb bank: mean similarity `direct↔doublespeak`
= **0.239**, `neutral↔doublespeak` = **0.255**, exact-word-swap-identical = **0/900**. Typical lengths
86 / 88 / 378 chars — i.e. Doublespeak carries ~292 extra characters of context that Direct and Neutral
do not have.

Note the file header of `30_build_pair_benchmark.py` claims conditions are "structurally matched: every
one has a demo block of the same size". That claim is **true for the semantic family and false for the
behavioral family**. For ASR a no-context Direct baseline is defensible; for *representation* comparisons
at the codeword position it is a length/context confound.

**Design response:** the Boombness generator emits `DIRECT_WITH_DEMOS` and `BENIGN_WITH_DEMOS` arms so
every condition carries a demo block of matched size and matched sentence frames.

#### F3 (§5.4, §10.3) — a Boombness direction ablation has ALREADY been run here, and it is a negative

Scouting turned up prior, uncommitted work I did not know about: `doublespeak_causality/scripts/phase4_bombness_intervention.py`
plus direction bundles `outputs/phase4_directions/v_bomb_*.pt` and 15 run dirs `outputs/phase4_bombness_*`
(2026-08-14/15). The existing `v_bomb[L]` is the unit diff-of-means **(doublespeak − benign) at
`codeword_last`**, over the write/carry band `L8–21`, shipped with `v_bomb_perp_ref` (orthogonalized
against refusal-L18), a norm-matched `v_random` control, and a per-layer `gap` dose unit.

Aggregating the most recent AdvBench/Llama-3.1-8B run (`phase4_bombness_full_advbench_..._758964`,
n=230, patch band L8–18, α=1.0, readouts L20/24/28/31 — scalars only):

| arm | ASR (judge = MALICIOUS) | mean judge score | bombness readout L20 / L24 / L28 / L31 |
|---|---|---|---|
| `ds_base` | 0.2043 | 0.1826 | −0.388 / −0.048 / +0.212 / +10.373 |
| `ds_bomb_ablate` | 0.2217 | 0.2005 | **−1.218 / −1.081 / −1.109 / +7.664** |
| `ds_bomb_random` | 0.1957 | 0.1826 | −0.376 / −0.040 / +0.222 / +10.429 |

Paired Δ(judge score) vs base: **ablate = +0.0179, 95% CI [−0.0001, +0.0360]**; random = 0.0000,
CI [−0.0111, +0.0111].

**Read:** the intervention *demonstrably works on the representation* — the bombness readout is driven
negative at every readout layer, while the norm-matched random direction moves it not at all. And ASR
does **not fall**; if anything it drifts marginally up. This is the plan §18 **outcome-B/C signature**
(representation manipulable, behavior unmoved) and it is consistent with the repo's established result
that *refusal suppression, not concept content, is the causal locus*
(`project_continuation_v2_complete`, `project_causal_circuit_sprint`).

**Why the sprint is still worth running (this is the sharpened hypothesis):** `v_bomb = doublespeak − benign`
is measured with the surface word held constant (`carrot` in both arms) and the demo domain varying — so
under the F1 2×2 it is the **context main effect**, not the surface-identity effect. It is also fitted
against the misaligned benign arm (F1). The plan's actual claim — "`carrot` acquires a hidden
representation that is increasingly *bomb*-like" — is a claim about movement along the
**surface-identity axis**, which is a *different direction*:

```
d_surface := ½[ (B − C) + (E − A) ]     # "bomb token minus carrot token", context matched
d_context := ½[ (C − A) + (B − E) ]     # what the existing v_bomb approximates
Boombness(h) := <h, d_surface>          # A low, B high; the question is where C lands
```

So the sprint's job is to redo the gate with the **unconfounded** `d_surface`, plus the interaction term
`(B−C) − (E−A)` which isolates what is doublespeak-*specific*. If the negative survives that, it is a
well-controlled negative worth publishing rather than a measurement artifact — which is exactly the
outcome the plan's §18-D asks us to be explicit about.

#### F4 (§2.4) — `carrot` and `bomb` do NOT tokenize symmetrically, and it hit the most important position

The mandatory tokenization audit (`src/boombness/tokenization_audit.py`, 1464 rows, Llama-3.1-8B-Instruct):

| variant | `carrot` | `bomb` |
|---|---|---|
| `" carrot"` / `" bomb"` | **1 token** | **1 token** |
| `"carrot"` / `"bomb"` (no leading space) | **2 tokens** `['car','rot']` | 1 token |
| `"Carrot"` / `"Bomb"` | 2 tokens | 1 token |
| `" Carrot"` / `" Bomb"` | 2 tokens | 1 token |

`bomb` is one token in essentially every surface form; `carrot` is one token **only** with a
leading space and lowercase. Measured over the first full bank: `bomb` was 1 subtoken in
2664/2664 occurrences, `carrot` in 4918/5808 — **890 two-subtoken occurrences**, and 558/1464
prompts contained a mix of widths.

Two distinct causes, both now fixed:

1. **The query template.** `the word "{W}"` renders `"carrot"`, and the opening quote steals the
   leading space → `['"','car','rot','"']`. This hit **the final query occurrence — the single
   most load-bearing position in the sprint** — in 516/516 semantic rows. Quotes around the
   target were removed from every query and mapping template.
2. **Sentence-initial demo sentences** ("Carrots can be stored…") → 374 occurrences. `demo_pools._clean`
   now requires the occurrence to be preceded by a space, so it is never sentence-initial.

**Why this mattered rather than being cosmetic:** the house readout position is `codeword_last`,
the *last* subtoken of the occurrence. For a 2-subtoken carrot that is the vector at `"rot"` —
a different vector entirely, and not comparable to the `" bomb"` vector it is differenced against
in `d_surface`. Left unfixed it would have put a systematic, arm-asymmetric error straight into
the direction estimate and the logit lens, in the direction of *understating* Boombness in the
carrot arm. After the fix every occurrence in both arms is exactly one token.

`extract_boombness.py` now records `n_subtokens` / `is_single_token` per occurrence regardless,
so any residual case can be conditioned on rather than averaged over.

- Next: await scouts, then write `src/boombness/prompt_families.py` implementing the 2×2 + plan axes.

### 2026-08-16 — Tick 1 (Phase 1 complete, Phase 2 submitted)

**Phase 1 DONE.** The bank is `data/boombness_prompts/boombness_prompt_bank.jsonl`:

| | |
|---|---|
| rows | 1464 |
| matched 2×2 families | 180 checked, **0 alignment violations** |
| token-level families | 540 checked, **0 token-alignment violations** |
| target occurrences | 8472, **all single-token in both arms** |
| conditions | benign_literal 348 · natural_doublespeak 540 · direct_harmful 216 · concept_in_benign_ctx 216 · direct_codeword 72 · benign_remap 72 |
| blocks | core2x2 864 · extra_conditions 144 · families 144 · role_style 120 · strength 96 · consistency 72 · position 24 |
| query kinds | behavioral 660 · semantic_one_word 516 · comprehension_usage 288 |
| n_examples | 0:240 · 1:144 · 2:192 · 4:468 · 8:276 · 16:144 |
| pools | `demo_pools.json` sha16 `3c430bec89d32db9`, 18 pools × 40 sentences (6 domains × {benign, harm, filler}) |

Manual review of `manual_review_50.md` plus a direct read of one example per axis confirmed every
axis renders as intended: `tool` / `cot_like` / `system_like_quoted` wrappers, `irrelevant`
(distractor word `tulip`, so the query codeword has no demo support — occurrences drop to 1 by
design), `conflicting` (counter-mapping sentence appended), `mixed` (half harm / half benign),
`distributed` (demos interleaved with word-free filler), `aggressive` (statement ×3), `direct_codeword`.

**Two defects the Phase-1 checks caught before any GPU time was spent** — both would have been
invisible in results:

| # | Defect | Detected by | Blast radius if shipped |
|---|---|---|---|
| 1 | Pool filter counted substrings (`"bombing"` passes) while span-finding used whole words | `check_alignment` — 114/180 families | 2×2 arms carry different occurrence counts → position-matched patching compares the wrong tokens |
| 2 | `carrot` is 2 tokens without a leading space (`"carrot"`, `Carrot`), `bomb` is 1 in every form; quoted query `the word "{W}"` hit **the final query occurrence in 516/516 semantic rows** | `tokenization_audit` — 890/5808 carrot occurrences at 2 subtokens | `codeword_last` reads the vector at `"rot"`; `d_surface` and the logit lens acquire a systematic arm-asymmetric error |

Both fixed, bank regenerated, both checks now clean. See F4 above.

**Phase 2 submitted.** SLURM job **760588** on `n-805` (`src/boombness/slurm/run_boombness.sh`,
L40S-guarded, cpus=4 mem=48G per the house fast-allocating footprint), running
`extract_boombness.py --stage both --limit 24` as the plan §2.3 smoke before the full sweep.

### 2026-08-16 — Tick 2 (Phase 2/3 smoke green, full extraction prepared)

**SLURM 760588 (smoke extraction) COMPLETE, 0 failures.** `--limit 24`, Llama-3.1-8B-Instruct on
n-805 (4 min weight load, ~3 min compute). Run dir
`outputs/boombness/extract_boombness/smoke_20260816_183101_1000604`, contract complete
(`config.json` / `metadata.json` / `results.jsonl` / `summary.json` / `RUNMETA.json` / `DONE.json` /
`plots/` / `cache/`), 28 attempted / 28 succeeded / 0 failed, 36 occurrence rows.

First look at the direction norms (fit on 1 family per cell — **noisy, not a result**, but the
structure is worth recording because it is the first evidence on the F1 question):

| ‖·‖ | L0 | L4 | L8 | L12 | L16 | L20 | L24 | L28 |
|---|---|---|---|---|---|---|---|---|
| `d_surface` | 1.79 | 4.78 | 7.17 | 8.61 | 13.02 | 19.35 | 27.36 | 34.74 |
| `d_context` | 0.08 | 0.98 | 2.37 | 3.12 | 2.99 | 3.71 | 5.90 | 9.28 |
| `d_inter` | 0.13 | 1.51 | 3.49 | 4.91 | 5.22 | 6.68 | 10.63 | 16.23 |
| `d_naive` | 1.79 | 4.86 | 7.66 | 9.06 | 13.27 | 20.07 | 29.31 | 38.13 |

`‖d_surface‖ ≫ ‖d_context‖` at every layer, and `d_naive ≈ d_surface` — i.e. the plan's naive
direction is dominated by the surface-word effect, with the context effect a much smaller
component. With n=1 per cell, `d_context` and `d_inter` are differences-of-differences of single
samples and are largely noise; the full fit (240 rows, 60 per cell per split) is what decides this.

**Token-id check passed:** concept first-ids `[13054, 33909, 79444, 92826]`, codeword first-ids
`[3341, 7063, 9028, 75294]` — disjoint, so `p_concept` and `p_codeword` are not partly the same
number. `score_behavior.py` now hard-fails if that ever stops holding.

**Optimization before the full run.** The scoring loop made one `lm_head` call per (layer, position)
pair — ~101k calls for the full bank, nearly all of it host/device round-trip rather than the
4096×|V| matmul. Added `signals.logit_lens_boombness_batch` and batched every (layer, position)
pair of an occurrence into one call (~12× fewer). Re-running the smoke as **760594** to confirm the
optimized path is numerically identical before committing GPU hours to the full sweep.

**New this tick:** `src/boombness/score_behavior.py` (plan §5.3/§8/§9) — forward-only readouts for
the semantic and comprehension query kinds, generation for the behavioral rows into a separate
`gens.jsonl`, with judging deliberately deferred to a CPU/API step so ASR can be recomputed at any
threshold without regenerating. Also `analyze_boombness.py` (plan §6.4/§7).

**Self-review in flight:** a 5-lens adversarial review workflow over the whole module (positions,
directions, generator, run contract, analysis), each finding independently double-refuted before it
counts.

**Batching verified equivalent (760594 vs 760588).** `src/boombness/compare_runs.py` compares every
shared numeric column row-by-row. Result: **every substantive metric agrees to ≤ 3.05e-5**
(`llfollow|L24|boombness`; probabilities to ≤ 3.6e-7) — ordinary float32 reduction-order difference
between a batched and an unbatched matmul.

**One metric did NOT agree, and it is a finding rather than a bug:** `rank_concept` moved by up to
**283 ranks out of 128256**. Two causes compound. (a) The old code read the argsort *position*,
which is arbitrary inside a tie block; the new code uses competition rank (count of strictly
greater logits), which is deterministic and is the better definition. (b) More importantly, the
float32 logit distribution has a very flat tail, so tie/near-tie blocks are hundreds of tokens wide
and a 1e-7 logit perturbation reorders them. **Conclusion: `rank_concept` is ill-conditioned
wherever it is large and must be treated as a coarse diagnostic only (meaningful below ~100), never
as a quantitative metric.** Documented in `signals.py`; `compare_runs.py` now classes `rank`
columns as soft so they cannot silently gate a submission. Everything quantitative uses
`logit_lens_boombness` or the probability mass instead.

**SLURM 760596 submitted:** full extraction, all 1464 bank rows, all 32 layers, logit lens at
L0/4/8/12/16/20/24/28/31, caching final-occurrence reps for the Phase-3 probes, 6h limit,
nodelist `n-802,n-803,n-805,t-806` (n-801 omitted — every weight load slower than 15 min in 232
logged runs happened there).

### 2026-08-16 — Tick 3 (self-review caught a result-corrupting bug; full run cancelled, fixed, relaunched)

The adversarial self-review workflow returned its first finding while job 760596 was scoring, and it
was real. **Both entries in the audit table above were found and fixed this tick**, and the full
extraction was cancelled at 600/1464 rows and resubmitted.

The first one is the kind of bug this sprint is supposed to be paranoid about, so it is worth
stating plainly: `logit(concept) − logit(codeword)` was aggregating over "the first token of every
surface variant of the word". For `bomb` that is four tokens all spelling *bomb*. For `carrot` it is
`[' carrot', 'car', 'Car', ' Car']` — **three of the four are the ordinary English word "car"**.
So the codeword side of every logit-lens score was inflated by car-the-vehicle, by a
context-dependent amount, and **only on one arm of the 2×2**. That is precisely the shape of error
that would have produced a confident, wrong Boombness curve. It did not crash, and no output looked
wrong.

Fix: `signals.readout_ids` / `readout_id_pair`, defaulting to one leading-space whole-word token per
side — `' bomb'` (13054) vs `' carrot'` (75294). Symmetric by construction, and it is the exact
token the generator guarantees appears in the prompt. `full_word` mode is retained as a robustness
check but is explicitly *not* the default, because it is asymmetric in count (4 vs 1) and the
scorers aggregate with `max()`, so more variants can only raise a score.

Writing that guard immediately caught a second one: the comprehension forced choice offered the
answer word `codeword`, which is **3 tokens** (`[' cod','ew','ord']`), so the single-next-token
readout was measuring the mass on `' cod'`. Answer vocabulary is now `literal` / `coded`, both
single tokens.

**Re-verified after both fixes:** bank 1464 rows / 180 families / 0 alignment violations;
tokenization audit 1464 ok / 0 bad / 0 ambiguous, 540 families / 0 token-alignment violations;
manual review sample regenerated.

**SLURM 760598 running** (full extraction, corrected readout ids).

### 2026-08-16 — Tick 4 (self-review: 26 candidates → 6 confirmed; FIRST BOOMBNESS RESULT)

The adversarial self-review workflow finished: **26 candidate findings, 6 confirmed** after each was
independently double-refuted (57 agents). All six were real. Two were fixed in Tick 3; the other four
are fixed here.

| # | Confirmed finding | Fix |
|---|---|---|
| 1 | `all_first_ids` put generic `car` on the codeword side of every logit-lens score | `readout_id_pair` (Tick 3) |
| 2 | comprehension answer `"codeword"` is 3 tokens → unanswerable forced choice | `literal`/`coded` (Tick 3) |
| 3 | **Top-layer logit lens applies the final norm twice.** transformers 5.12 ties `hidden_states[-1]` to `last_hidden_state` (`output_capturing.py:265-267`, `tie_last_hidden_states=True`), which for Llama is `norm(final block output)`. So `hs[L+1]` was the raw block residual for every L **except the last**, where it was post-norm — the lens then normed it again, and `d_surface[31]` was fitted in different coordinates from every other layer. | `forward_hidden` now captures `layers[-1]`'s true output with a forward hook and substitutes it, so `hs[L+1]` is uniform in L. A `_diag` field records the raw-vs-tied discrepancy so the correction is demonstrated, not asserted. |
| 4 | **Additive doses were ~10× too small.** `estimate_directions` stores UNIT vectors with the effect size in `gap`, but `aggressive_patching` applied `h += alpha·d_unit` with `alpha ≤ 8`, while the measured gaps are ‖d_surface‖ ≈ 6–32. The additive arm would have reported "adding Boombness does nothing" as a pure dose artifact — exactly the false negative this gate must not produce. | `alpha` is now in **gap units** (`alpha=1` = one diff-of-means), with controls scaled by the same gap so they stay norm-matched. `--dose-unit absolute` reproduces the old behaviour. |
| 5 | **`benign_remap` (cell F) applied no remapping.** It drew from the `benign` pool, whose natural word is *already* the codeword, and substituted nothing — so **72/72 F rows were byte-identical to a `benign_literal` row**. The control was numerically the same arm it was meant to be contrasted against. | New per-domain `remap` pools about `bicycle`, substituted onto the codeword, so the demos teach `carrot = bicycle`: same structure and same remapping operation as doublespeak, harmless meaning. `generate_bank` now asserts F never collapses onto A. |
| 6 | **Family alignment violations never reached the `FailureLedger`**, and `audit_family_alignment` returned `[]` for families it had never checked — so the audit reported "540 families, 0 violations" when only **216** were 2×2-complete and **324 were silently skipped**. My own Tick-1 coverage claim was overstated because of this. | Returns `None` for unchecked families; summary now reports `n_families_alignment_checked` / `n_families_skipped_incomplete_2x2`; every violation calls `ledger.fail`. |

Also hardened (candidates that did not survive double-refutation but are cheap insurance):
`stage_fit` now intersects the four cells' **family sets** and drops any family missing from any cell
(equal counts are not equal composition), recording the family-set hash; `_cross_fit_split` returns an
explicit `is_self_fit` flag recorded on every row.

#### FIRST BOOMBNESS RESULT (run `full_20260816_184609_1003374`, 1464 rows, 8472 occurrences, 0 failures)

Directions fitted on 30 families/cell/split, cross-fitted. Norms confirm the Tick-2 hint at full n:

| ‖·‖ | L0 | L8 | L16 | L24 | L28 |
|---|---|---|---|---|---|
| `d_surface` | 1.79 | 6.08 | 11.70 | 25.63 | 32.04 |
| `d_context` | 0.12 | 1.96 | 3.04 | 5.98 | 9.11 |
| `d_inter` | 0.23 | **4.09** | 6.29 | 10.84 | 15.65 |

`‖d_surface‖ ≫ ‖d_context‖` everywhere — and **`‖d_inter‖ > ‖d_context‖` at every layer**, i.e. the
*interaction* (is the surface effect itself context-dependent?) is a bigger term than the context main
effect. That is the doublespeak-specific quantity, and it is not small.

**The headline.** `Boombness = ⟨h, d_surface⟩` at the final query occurrence, per 2×2 cell, and the
key contrast `C − A` (doublespeak carrot vs benign-literal carrot — same token, same query, only the
demo valence differs). `(C−A)/(B−A)` is the fraction of the way from benign-carrot to direct-bomb:

| L | A benign | C doublespeak | E bomb/benign | B direct | **C−A** | sem | (C−A)/(B−A) |
|---|---|---|---|---|---|---|---|
| 0 | −0.629 | −0.632 | 0.601 | 0.598 | −0.003 | 0.000 | −0.002 |
| 4 | −0.540 | −0.529 | 0.492 | 0.490 | +0.011 | 0.004 | 0.011 |
| **8** | −0.465 | −0.426 | 0.423 | 0.460 | **+0.039** | 0.007 | **0.042** |
| 12 | −0.430 | −0.402 | 0.365 | 0.387 | +0.028 | 0.005 | 0.034 |
| 16 | −0.551 | −0.556 | 0.396 | 0.417 | −0.005 | 0.005 | −0.005 |
| 20 | −0.540 | −0.551 | 0.460 | 0.475 | −0.011 | 0.004 | −0.011 |
| 24 | −0.531 | −0.529 | 0.411 | 0.467 | +0.002 | 0.005 | 0.002 |
| 28 | −0.466 | −0.439 | 0.369 | 0.442 | +0.027 | 0.006 | 0.030 |
| 31 | −0.491 | −0.379 | 0.346 | 0.450 | +0.112 | 0.008 | 0.119 |

Three things stand out:

1. **The sanity check passes at all 32 layers** (concept-surface cells score above codeword-surface
   cells), and `C−A ≈ 0` at L0–L2 as it must — no context has been integrated yet.
2. **There is a real but small early effect peaking at L8** (+0.039, ≈5.5σ): the doublespeak carrot
   travels ~**4%** of the way toward the direct-bomb representation. L8 is precisely the write band
   this repo has localized before (`v_bomb` uses `range(8,22)`; the concept write was placed at L9).
3. **The middle layers L16–L22 are flat or slightly NEGATIVE**, then the effect returns late.

So the trajectory is two-humped — a write-band bump, a null carry band, a late-layer rise — and at no
point does the doublespeak carrot approach the bomb representation. That is already a much more
specific statement than "carrot becomes bomb-like".

> ⚠️ **The L31 number is NOT yet reportable.** The largest apparent effect (+0.112) sits at exactly
> the layer affected by confirmed finding #3 — this run predates the `forward_hidden` fix, so L31 was
> computed on post-final-norm vectors. The contrast is internally consistent (all four cells share the
> convention) but is not comparable to the other layers and may be partly an artifact. It will be
> re-measured in the corrected rerun before it is claimed. **L0–L30 are unaffected by that fix.**

### 2026-08-16 — Tick 5 (Phase 3 probes implemented; corrected extraction re-running)

- **SLURM 760611** (corrected full extraction, every confirmed fix in place) running on `n-805`.
  Weight load is slow this time (~7.5 min, 1.3–4.4 s/it vs 1.8 s/it earlier) — node contention, not
  a hang: the loading bar is advancing, which is the house diagnostic for telling the two apart.
- **`src/boombness/probes.py` added** (plan §6.3) and a pilot is running on the cached
  final-occurrence reps of the previous run.

The four probe regimes are deliberately ordered by how much they can be fooled:

| regime | train → test | what it can be fooled by |
|---|---|---|
| `d1_simple` | concept-surface (B,E) vs codeword-surface (A,C), all blocks | **lexical identity** — expected near-ceiling at L0 and worth nothing on its own |
| `d2_aligned` | same, restricted to matched 2×2 families | template memorization (removed by the domain split) |
| `d3_hard_negative` | same pool, metrics broken out **per cell** | conflating *concept-ness* with *harm-context-ness* — E (concept token, benign context) and C (codeword token, harmful context) are the two cells that separate those hypotheses, so their per-cell recall is reported rather than averaged away |
| `d4_heldout_ds` | **train with cell C removed, then score C** | nothing — this is the generalization test the plan asks for |

`p_C_minus_p_A` from `d4_heldout_ds` is the learned-classifier analogue of the `C−A` contrast in
`analyze_boombness`: a probe that never saw a doublespeak prompt is asked how concept-like the
doublespeak carrot looks, relative to the benign-literal carrot.

Two design choices worth stating because they are what keep the number honest:
- **Splits are by DOMAIN** (group-k-fold), never by row, so a probe cannot memorize a template and
  then score its twin.
- **Every regime is also run with SHUFFLED LABELS.** A shuffled-label AUROC meaningfully above 0.5
  means the split leaks and the real number is not interpretable. This is plan §2.5's shuffled-label
  control, and it is reported next to every headline AUROC rather than in an appendix.

Also fixed two minor review findings: `discover_columns` scanned only the first 200 rows (rows here
are heterogeneous, so a prefix scan could silently drop a metric), and `RunDir` now refuses to open
an existing run directory (`log_row` appends, so a reused directory would silently double its rows
and desynchronise the count from the failure ledger).

### 2026-08-16 — Tick 6 (probe pilot exposed two flaws in my own analysis; both fixed)

The probe pilot completed (1320 labellable prompts: C 540 · A 348 · B 216 · E 216, 3-fold over
domains, 0 missing reps). It ran clean and reported **AUROC = 1.0000 for every regime at every
layer** — which is not a result, it is a bug report about the probe.

**Flaw 1 — saturation.** Each fold trains on ~576 examples in **4096 dimensions**. At that ratio
the classes are almost surely linearly separable, so the logistic fit drives the margin to
saturation: `P(concept|A)` and `P(concept|C)` both came back as *exactly* 0.0, and their difference
— the graded quantity the whole probe exists to produce — was 1e-33 to 1e-9. A perfect classifier
carrying no information. Fixed by standardize → **PCA (fit on the training fold only, unsupervised,
so no leakage)** → L2 logistic. `--pca 0` reproduces the saturated behaviour so it can be
demonstrated rather than asserted, and every layer now reports a `saturation_frac` next to its AUROC.

**Flaw 2 — the shuffled-label control was not a control.** It came back at 0.58–0.64 rather than
0.5, which looks like a leaking split. It was not: I was reporting **argmax-over-layers for the real
arm and argmax-over-layers for the shuffled arm and comparing the two**. Both are maxima of nine
noisy estimates, so both are biased upward by selection, and the difference of two independently
selected maxima is not a comparison at all. Fixed: real and shuffled are now paired **at the same
layer**, the reported quantity is the per-layer `auroc_lift = real − shuffled`, and the headline
layer is chosen on the lift rather than on the raw AUROC. The full per-layer table is printed, so
`L0 = 1.0` (pure lexical identity) is visible as the artifact it is instead of being selected as
"the best layer".

This is the same selection-bias family the self-review flagged in `analyze_boombness.prompt_level`
(argmax over layers per prompt, then compare groups). Both now report the full curve.

- **SLURM 760611** still scoring; fit stage completed cleanly with the new guard:
  `dev families=30 sha16 e92f0ae8`, `heldout families=30 sha16 667cc4fa` — all four cells averaged
  over an identical, recorded family set, and the two splits disjoint.
- Probe rerun with PCA-64 and paired reporting is running.

### 2026-08-16 — Tick 7 (CORRECTED FULL RESULT — Phases 3 and 4 substantially answered)

Run `full_20260816_185942_1008673`: 1464 prompts, 8472 occurrences, **0 failures**, directions fitted
on 30 families/cell/split with recorded family-set hashes (`dev e92f0ae8`, `heldout 667cc4fa`,
0 cell-family entries dropped), **0 rows self-fitted** (every score is genuinely cross-fitted).

#### The last-layer fix was not cosmetic

The diagnostic `last_layer_tied_vs_raw_relnorm` came back at **mean 0.653, max 0.692** — the tied
(post-final-norm) and the true (raw block) last-layer vectors differ by ~65% of the vector norm.
They are not nearly the same vector. Everything previously computed at L31 was a different quantity.

**And the L31 effect ⚠(depth-mismatched — see C9) survived it, larger:** `C−A` went from +0.112 (contaminated) to **+0.133**
(corrected). So the late-layer rise is real, not a norm artifact — a good outcome for a check that
could equally have destroyed the headline.

#### Boombness `C−A`, paired within family (n=30 families, t on the paired differences)

`C−A` = doublespeak carrot minus benign-literal carrot: same token, same query, only the demo
valence differs. `frac` = `(C−A)/(B−A)`, the fraction of the way to the direct-bomb representation.

| L | 0 | 4 | **8** | 12 | 16 | 20 | 24 | 28 | **31** |
|---|---|---|---|---|---|---|---|---|---|
| mean | −0.003 | +0.017 | **+0.048** | +0.036 | +0.003 | −0.004 | +0.015 | +0.043 | **+0.133** |
| t | −6.8 | +5.6 | +5.3 | +5.4 | **+0.7** | **−1.1** | +2.5 | +5.9 | +14.0 |
| frac | −0.002 | +0.016 | **+0.052** | +0.045 | +0.003 | −0.004 | +0.015 | +0.048 | **+0.141** |

**A two-humped trajectory with a null in the middle:**
1. **Write hump, L4–L14, peaking at L8** (+0.048, t=5.3, ~5% of the surface distance). L8 is exactly
   the write band this repo localized independently (`v_bomb` uses `range(8,22)`; the concept write
   was placed at L9).
2. **Null carry band, L16–L22** (t = +0.7, +0.1, −1.1, +1.0) — no displacement along the
   surface-identity axis at all.
3. **Readout hump, L24–L31**, rising monotonically to +0.133 (t=14.0, ~14%).

At no layer does the doublespeak carrot approach the bomb representation. "Carrot becomes bomb-like"
is too strong; "carrot is displaced a few percent toward bomb, in two specific layer bands, with a
null between them" is what the data supports.

#### Convergent validity: the held-out probe reproduces the same profile

`probes.py` regime `d4_heldout_ds` trains with cell C **entirely removed** and then scores it. The
graded score is the decision-function margin (`margin_C_minus_A`, normalized as `fracC`):

| L | 0 | 4 | **8** | 12 | 16 | 20 | 24 | 28 | 30 |
|---|---|---|---|---|---|---|---|---|---|
| fracC | +0.007 | +0.043 | **+0.066** | +0.062 | −0.010 | −0.025 | −0.013 | +0.012 | +0.038 |

Same shape from a completely different estimator: hump peaking at L8, **null/negative at L16–L24**,
rise at L28–L30. A diff-of-means direction and a linear classifier that never saw a doublespeak
prompt agree on the layer profile and roughly on the magnitude (5% vs 6.6% at L8).

#### The naive direction inflates the effect ~2× and manufactures signal where there is none

This is the empirical payoff of the F1 design change. Same rows, same contrast, `d_naive = B−A`
(what plan §6.2 asks for) versus the identified `d_surface`:

| L | 4 | 8 | 12 | **16** | **20** | 28 | 31 |
|---|---|---|---|---|---|---|---|
| `d_surface` frac | +0.016 | +0.052 | +0.045 | **+0.003** | **−0.004** | +0.048 | +0.141 |
| `d_naive` frac | +0.046 | +0.091 | +0.094 | **+0.030** | **+0.017** | +0.085 | +0.216 |

`d_naive` roughly **doubles** the effect at every layer, and in the carry band L16–L20 it reports a
clearly positive effect (+0.030, +0.017; t=+6.4, +4.3) where the identified direction finds **zero**.
That difference is exactly `d_context` — the confound. Had we used the plan's direction we would have
reported a monotone, everywhere-positive Boombness curve and missed the null band entirely.

#### The naive diagonal probe learned CONCEPT-ness, not harm-context-ness

Regime `d3_hard_negative` trains on the easy diagonal A vs B only, then tests on the off-diagonal:
**recall on E = 1.00 and recall on C = 1.00 at every layer.** A probe that had learned
"harm-context-ness" would get both exactly backwards. So the surface-identity signal is genuinely
about the token's concept identity and is not confusable with the context valence — which is why
the small `C−A` displacement is interpretable as movement along a concept axis at all.

#### Where the metrics disagree, and why that is not a contradiction

The logit lens gives a *different* picture early: `C−A` is **negative** at L0–L20 (−0.65 to −2.38,
|t| up to 14.7) and positive only at L28/L31 (+2.08, +5.92). This is reported as a distinct
construct, not as a refutation: the logit lens at the carrot position decodes the **next-token
prediction**, and in a doublespeak demo the token after `carrot` is a harm predicate ("exploded",
"was defused"), so the lens is reading local continuation rather than the token's own concept
identity. Two constructs, two answers; the direction and probe metrics measure the token's own
representation and agree with each other.

**Phase 3 (§6) and Phase 4 (§7.1) are substantially answered.** Remaining for Phase 4: the
example-count sweep (§8) plots are generated but not yet written up.

### 2026-08-16 — Tick 8 (Phase 2 + Phase 5 launched; 4-hourly independent audit running)

Every 8th tick carries an independent audit, and this is it. The audit is deliberately pointed at
the **tick-7 claims themselves**, not just the code — four auditors, each told to try to break a
specific claim, with every finding independently refuted before it counts:

| auditor | job |
|---|---|
| `outputs-vs-claims` | recompute `C−A` from `results.jsonl` and check the two-humped shape, the n=30, the zero self-fits, and whether the L16–L22 null survives changing the subset |
| `new-code` | the `forward_hidden` hook, the `stage_fit` family intersection, and — the one I most want checked — whether probe margins from **different folds** (each with its own scaler/PCA/classifier) are comparable at all, since pooling incomparable margins would invalidate `margin_C_minus_A` |
| `statistics` | are 30 families independent when they share pools and domains? is the "null" actually powered to exclude an L8-sized effect, or should it be downgraded to "not detected"? do the effects survive multiple-comparison correction across 32 layers? is "two-humped" a formal result or pattern-matching on a 32-point curve? |
| `provenance` | **`prompt_id = sha256(family_id + condition)` does not hash the prompt TEXT** — and the bank has been regenerated several times with changed content, so two runs could share a `prompt_id` while referring to different prompts |

That last one I flagged to the auditor myself: it is a latent provenance hazard I introduced in
Phase 1 and have not yet fixed.

**Jobs submitted:**
- **760661** `aggressive_patching.py` smoke (plan §5) on `n-802` — the Phase-2 decision gate G1.
- **760663** `score_behavior.py` smoke (plan §5.3/§9) on `n-801` — the first step toward gate G2.

`bscore` was initially submitted as 760662 and sat **PENDING (Resources)**; per the house rule that
no job should sit queued, it was cancelled and resubmitted with a wider nodelist, and started
immediately.

**Provenance hazard fixed (self-identified, before the audit reported).** `prompt_id` is
`sha256(family_id + condition)` — it names "this cell of this family" and deliberately stays stable
across bank versions so matched rows can be joined. On its own that is a hazard: the bank has been
regenerated several times with changed content (the `benign_remap` fix rewrote 72 prompts), so two
runs could be joined on `prompt_id` while referring to **different prompt text**, with nothing to
detect it.

Every row now also carries `prompt_sha16` (a hash of the prompt text), the bank meta carries
`bank_content_sha16` (`59ad8c8c44f7c3fa`), and `extract_boombness` / `score_behavior` record the
per-row content hash on every result row. Stale joins are now detectable rather than silent. The
identity id is kept as-is, because losing it would break the matched-family joins the whole 2×2
analysis depends on.

The new hashes also surfaced a benign fact worth recording: the bank has **1464 distinct
`prompt_id` but 1238 distinct prompt texts**. All 240 duplicate rows are `n_examples=0` — the
degenerate baseline where, with no demonstrations, every condition collapses to the bare query by
construction. **Zero duplicates among prompts with demonstrations**, and the direction fit uses only
`n_examples>0`, so no degenerate row enters any estimate.

**Quantifying the dosing fix (confirmed finding #4) against the real fitted gaps.** From
`directions_fit_dev.pt`: `‖d_surface‖ = 6.05` at L8 and `14.79` at L18. Under the old unit-vector
dosing the smoke's `alpha ∈ {0.5, 1, 2}` would have injected a flat 0.5/1/2 of residual magnitude —
i.e. **8% / 17% / 33% of one diff-of-means at L8, and only 3% / 7% / 14% at L18**. The additive arm
would have been probing a small fraction of the natural effect size and would almost certainly have
returned "adding Boombness does nothing", which the plan would have read as a causal negative.

In gap units `alpha=1` now injects exactly one diff-of-means (6.1 at L8, 14.8 at L18) and `alpha=2`
twice that. This is what makes the §5.2 additive sweep a real test rather than a foregone conclusion.

### 2026-08-16 — Tick 9 (G1 smoke found two more measurement bugs; machinery otherwise verified)

**The transplant machinery is verified correct.** The live self-swap invariant — replace a prompt's
own captured states at its own positions — is an **exact** no-op: `|baseline − self_swap| = 0.00e+00`
on all four families. That is the check that says a null result later would be a real null rather
than a hook that never fired.

**Two measurement bugs, both found by the smoke, both silent, both now fixed** (see the audit table):
readouts at the patched layer were pre-patch, and the L31 readout used post-norm coordinates against
raw-fitted directions. The first is the more insidious: it would have made every intervention look
like it had *no effect at the layer it was applied to*, which is exactly the shape of a false causal
negative. Smoke 760661 discarded; **760681** resubmitted.

**A third problem, not yet fixed — the semantic readout is dead.** Across every arm including the
donor ceiling, `p_concept` and `p_codeword` are ~1e-6 to 1e-5, so `semantic_margin` is numerically
zero everywhere:

| arm | p_concept | p_codeword |
|---|---|---|
| baseline (doublespeak) | 6.5e-06 | 2.6e-06 |
| donor ceiling (direct bomb) | 5.2e-06 | 4.4e-08 |

The `semantic_one_word` query asks "what does the word X actually refer to?", but the model's
**immediate next token** is evidently not the answer word — it is presumably a preamble token. So
the next-token readout measures nothing, in every arm, and any §5.2/§5.3 conclusion drawn from
`semantic_margin` would be a conclusion about a number that is always zero. The *representation*
readouts (boombness cosine, logit lens) are unaffected and are working.

This needs the actual next-token distribution inspected before the readout is trusted; it is the
next thing to fix. Recorded here rather than worked around, because "the metric was flat" is exactly
how a dead readout gets mistaken for a negative result.

#### G1 partial answer (smoke2 `smoke2_20260816_194436_3945609`, 472 rows, 0 failures)

Both invariants hold after the `BlockCapture` fix: patching at L8 now moves the L8 readout
(−0.2294 → **+0.1272, exactly the donor's own L8 value**, which is what a correct transplant must
produce), and the self-swap is still an exact no-op (0.00e+00 across all layers and families).

Boombness `⟨h, d_surface⟩` at the query position, `harm_ctx` pair (recipient = doublespeak,
donor = direct):

| arm | L8 | L16 | L18 | L24 | L31 |
|---|---|---|---|---|---|
| baseline (doublespeak) | −0.229 | −0.301 | −0.313 | −0.326 | −0.052 |
| donor ceiling (direct) | +0.127 | +0.238 | +0.288 | +0.260 | +0.231 |
| **transplant, query only, L8 alone** | +0.127 | **+0.291** | **+0.392** | **+0.336** | **+0.275** |
| transplant, query only, L18 alone | −0.229 | −0.301 | +0.288 | +0.249 | +0.199 |
| **transplant, demos only, L8–21** | −0.229 | −0.343 | −0.361 | −0.371 | −0.063 |
| add `d_surface` α=1 (L8–21) | +0.593 | +0.804 | +0.821 | +0.717 | +0.199 |
| add **random** α=1 | −0.168 | −0.013 | −0.033 | +0.002 | +0.051 |
| add **orthogonal** α=1 | −0.167 | −0.036 | −0.030 | +0.005 | +0.053 |

**Plan §5.4 questions 1, 6 and 7 are answered on the representation side:**

1. *Can we force `carrot` to be internally `bomb`-like?* **Yes, easily.** A single-layer transplant
   at L8 flips the query token from −0.23 to +0.13 and the effect **propagates and amplifies** —
   downstream it lands *above* the genuine direct prompt (+0.392 vs +0.288 at L18).
6. *Which token positions matter?* **The query position, and only it.** Transplanting the
   **demonstration** carrots across the whole L8–21 band does **nothing** to the query token
   (−0.229 → −0.229 at L8; slightly *more* codeword-like downstream). The query token's
   representation is not inherited from the demo positions in this band.
7. *Which layers?* **L8 alone suffices** — patching only L8 reproduces or exceeds the full-band
   effect at every downstream readout. Patching at L18 alone affects L18 onward but leaves L8/L16
   untouched, as causality requires.

Controls pass: norm-matched **random** and **orthogonal** directions at the same dose barely move
the readout (+0.06 drift at L8 versus +0.82 for `d_surface`), so the effect is axis-specific and not
a generic perturbation.

**Two caveats, stated plainly:**
- The additive arm is partly **circular**: adding `d_surface` and then measuring `⟨h, d_surface⟩`
  must increase by construction. Its value is as a *dose-response tool for the behavioural readout*,
  not as evidence in itself. The transplant arm is not circular — the donor state is measured, not
  constructed.
- The `benign_ctx` control pair behaves **almost identically** to `harm_ctx` (e.g. L18: −0.230 →
  +0.383 vs −0.313 → +0.392). So forcing a carrot to be bomb-like works the same **whether or not
  doublespeak context is present**. Whatever the transplant is doing, it is not doublespeak-specific.

**G1 remains OPEN** on the question that decides it — *does any of this change behaviour?* — because
the behavioural readout is the dead `semantic_margin`. Diagnostic job **760683** is testing three
framings (as-is / assistant-primed / house-style forced choice) to find one that puts real mass on
the answer words.

### 2026-08-16 — Tick 10 (the "dead readout" was TWO bugs, and neither was the readout)

I reported last tick that the semantic readout was dead. That was the wrong diagnosis, and the
correction matters more than the original observation.

**Bug A — the wrong statistic.** `semantic_margin` was `p_concept − p_codeword`. A safety-tuned chat
model does not open its answer with the bare answer word, so both candidates sit deep in the tail,
and a *difference of probabilities* there is dominated by the larger term and discards everything.
On the same smoke rows:

| cell | p_concept | p_codeword | p-difference (what I used) | **log-odds (correct)** |
|---|---|---|---|---|
| A benign_literal | 1.8e-12 | 5.3e-05 | −5.3e-05 | **−17.19** |
| C natural_doublespeak | 3.4e-06 | 1.1e-04 | −1.1e-04 | **−3.50** |
| B direct_harmful | 6.3e-07 | 1.8e-09 | +6.3e-07 | **+5.83** |

`p_concept` differs between the benign and doublespeak arms by a factor of ~2 million, and the
subtraction rendered it as "both ≈ 0". In log space the arms separate by **13.7 log-units**. Both
readouts now report log-odds as primary (computed in log space, never by exponentiating and
re-logging), with the p-difference kept only as a diagnostic.

The comprehension control is alive too, and correct: it calls the benign carrot **literal**
(−2.94) and the doublespeak carrot **coded** (+2.06). §2.6's control works.

**Bug B — the smoke was scored entirely on degenerate prompts.** `--limit N` took the *first* N bank
rows, and the generator emits `n_examples=0` first. Those are the zero-demonstration baseline where
every codeword-surface condition **is** the bare query — the model has nothing to answer from, which
is why `A` and `C` came back byte-identical in the smoke. `--limit` is now a **stratified round-robin
over (query_kind, condition, n_examples)**, so a smoke exercises real prompts.

**What the diagnostic (job 760683) showed on real n=4 prompts** — three framings, `p` on the answer:

| framing | direct | doublespeak | benign |
|---|---|---|---|
| as-is ("what does X refer to?") | 1.4e-02 | 1.3e-03 | 1.2e-08 |
| assistant-primed | 2.4e-02 | 2.8e-02 | 1.5e-07 |
| **forced choice (both options named)** | **0.979** | 0.028 / 0.482 | 7.4e-06 |

The forced-choice framing concentrates mass on the answer (0.979 for direct) and is the house
framing (`46_forced_choice_patchscope`) for exactly this reason. Added as query kind
`semantic_forced_choice`; bank now 1752 rows.

**A first read of the effect size, from the as-is diagnostic:** in log-odds the benign arm is −6.0,
doublespeak +2.8, direct +15.8 — so the doublespeak prompt sits **~40% of the way** from benign to
direct on what the model *says the word means*, while the token's representation moved only ~5%
along `d_surface` at L8. Those are different quantities and the gap between them is itself worth
investigating; not yet a claim, n=2 prompts.

**Invariant scoping.** A forced-choice query names both words, so the exact-swap invariant genuinely
cannot hold on the full prompt (swapping would turn "a carrot or a bomb" into "a carrot or a
carrot"). `check_alignment` now applies it to the **demo block** for those kinds, and the
tokenization audit reports such families as **not checked** rather than passing — the same
skipped-vs-passed distinction the earlier audit got wrong. Rebuilt clean: 1752 rows, 240 families,
**0 character-level and 0 token-level violations**, 1752 rows ok / 0 bad / 0 ambiguous.

---

## ⛔ RETRACTION — the Tick-7 headline result does not survive audit

The 4-hourly independent audit (tick 8, 34 agents) returned **30 candidate findings, 25 confirmed**
after independent refutation, **9 of them result-corrupting**. Four directly invalidate the tick-7
claims. **Treat the Tick-7 section above as superseded by this one.** It is left in place
un-edited, because a research log that quietly rewrites its own errors is worth less than one that
shows them.

### What I claimed, and what is actually true

`reanalyze_corrected.py` recomputes the same contrast with the corrections applied. Contrast is
`C−A` on `d_surface|cos`, paired within family, **domain-clustered** SEs, Holm across layers.

| # | Tick-7 claim | Verdict |
|---|---|---|
| 1 | "Two-humped profile with a **null carry band** at L16–L22" | **FALSE.** The band is not null; it is significantly **NEGATIVE** (L20 = −0.029, t=−4.2). The "null" was an artifact of restricting to one query kind. |
| 2 | "L8 write hump, +0.048, t=5.3" | **DOES NOT SURVIVE.** Under domain-clustered inference t falls 5.3 → 3.3, and Holm across 32 layers **rejects** it (p=0.022). |
| 3 | "The held-out probe reproduces the profile independently" | **VOID.** The probe run scored a **superseded extract run** (`…184609_1003374`), not the headline run. Those runs differ at *every* layer because the bank was regenerated between them — 7527/8472 rows have different token positions. Not two estimators on the same rows; two data generations. |
| 4 | "L31 = +0.133, and the last-layer fix caused +0.112 → +0.133" | **BOTH WRONG.** Pooled over query kinds L31 is **+0.047**, not +0.133 — the unreported behavioral-only restriction nearly tripled it. And the +0.112 → +0.133 delta is **confounded with the bank regeneration**: layers the norm-tie cannot touch also moved (L20 went from −0.011, t=−3.1 *significant*, to −0.004, "null"). |

### What the data actually shows

**(a) Query kind drives the result, and I restricted to one without saying so.**

| L | behavioral | comprehension | semantic | **pooled** |
|---|---|---|---|---|
| 8 | +0.048 (t+2.1) | +0.017 (t+4.5) | +0.017 (t+4.4) | +0.027 (t+3.3) |
| 20 | −0.004 (t−0.6) | **−0.037 (t−4.6)** | **−0.046 (t−4.2)** | **−0.029 (t−4.2)** |
| 31 | **+0.133 (t+9.8)** | +0.000 (t+0.0) | +0.009 (t+1.9) | +0.047 (t+10.5) |

The L31 heterogeneity is severe (+0.133 vs +0.000): a pooled number across components that
disagree that much is itself of limited meaning, and is flagged rather than headlined.

**(b) The "null" was a cancellation across demonstration count — and the sign is the opposite of
the plan's hypothesis.** `C−A` pooled over query kinds, by `n_examples`:

| L | n=1 | n=2 | n=4 | n=8 | n=16 |
|---|---|---|---|---|---|
| 20 | −0.002 (t−0.6) | −0.015 (t−1.1) | −0.037 (t−3.6) | **−0.051 (t−9.2)** | −0.042 (t−5.5) |
| 31 | +0.049 | +0.046 | +0.049 | +0.044 | +0.050 |

**More demonstrations make the doublespeak carrot *less* bomb-like through the middle layers**, not
more. The plan predicts the opposite. The L31 effect, by contrast, is flat in `n_examples`.

**(c) Only two layers survive Holm under clustered inference:** L4 (+0.023, p=0.0016) and L31
(+0.047, p=0.0001). The L8 hump does not.

**(d) A null needs an interval.** The non-significant layers can only exclude effects larger than
**24–34% of the largest observed effect**. So "no effect at L8/L16/L24" is not supportable; the
honest statement is **"not detected, and underpowered to exclude an effect a third the size of the
L31 one."**

### Why this happened, and what changes

Root causes, all mine: an **unreported subset restriction** (behavioral-only); **pseudo-replication**
(60 rows treated as 60 independent draws when they are 6 domains × nested example counts × 2
splits); **no multiplicity correction** over 32 layers; **asserting a null from p>0.05**; and
**joining across bank regenerations** via a `prompt_id` that does not hash prompt text — the exact
hazard I had identified and flagged to the auditor one tick earlier, while a stale comparison built
on it was already in the log.

Process changes: `reanalyze_corrected.py` is now the reporting path (per-query-kind + pooled,
layer×n_examples surface, clustered SEs, Holm, intervals for nulls); no pooled number may be quoted
without its per-query-kind breakdown; the probes must be re-run against the headline run before any
convergence claim is restated.

### Code bug from the same audit, fixed

**The unit-vector dosing bug recurred.** I fixed it in `aggressive_patching` and missed the second
call site: `score_behavior.make_intervention` passed a bare `alpha` to `AllPositionAdd` on a unit
vector. At L18 (gap 14.8) `alpha=1` would have been ~7% of one diff-of-means, so every §10
intervention arm would have been under-dosed by ~14×. Now dosed in gap units, and it raises rather
than silently defaulting if `gap` is absent.

---

## Corrected result (replaces the retracted Tick-7 headline)

Probes re-run against the **headline** extract run (`headline_20260816_200516_2995581`,
`run_scored = full_20260816_185942_1008673`, L31 now included). The convergence claim I made
falsely at tick 7 can now be made properly, because both estimators finally read the **same
activations of the same prompts**.

`C−A` as a fraction of the codeword→concept span, two independent estimators:

| L | direction (pooled, domain-clustered) | probe `d4_heldout_ds` (trained with C removed) | sign |
|---|---|---|---|
| 0 | −0.0009 | +0.0070 | (both ≈0) |
| 4 | **+0.0230** | **+0.0498** | ✓ |
| 8 | +0.0272 | +0.0672 | ✓ |
| 12 | +0.0154 | +0.0656 | ✓ |
| 16 | **−0.0230** | **−0.0102** | ✓ |
| 20 | **−0.0293** | **−0.0348** | ✓ |
| 24 | −0.0206 | −0.0235 | ✓ |
| 28 | −0.0002 | +0.0034 | (both ≈0) |
| 31 | **+0.0473** | **+0.0886** | ✓ |

**Pearson r = 0.967, Spearman = 0.950** over 9 layers; signs agree at 7/9, and both disagreements
are at layers where both estimators are ≈0.

### The shape is three-phase, not two-humped

**positive (L4–L12) → NEGATIVE (L16–L24) → positive (L30–L31).**

The middle band is not a null and never was. The doublespeak carrot moves *toward* the concept
early, **away from it through the middle layers**, and toward it again at the very end. The
retracted "two-humped with a null carry band" was that middle negative phase averaged to zero by an
unreported query-kind restriction.

Two features make this more interesting than the original claim:
- The **middle-layer repulsion strengthens with demonstration count** (L20: −0.002 at n=1 →
  **−0.051 at n=8**, t=−9.2). More teaching pushes the codeword *further from* the concept in mid
  layers, which is the opposite of the plan's hypothesis.
- The **L31 effect is flat in demonstration count** (+0.044 to +0.050 across n=1…16) but **highly
  heterogeneous across query kind** (behavioral +0.133, comprehension +0.000, semantic +0.009).

### Caveats that stay attached to this result

1. **Not independent estimators in the strong sense.** Both read the same activations of the same
   prompts, so a shared error (a wrong position, a bad direction basis) would move both together.
   The agreement rules out *estimator-specific* error, not *data-level* error.
2. **Only L4 and L31 survive Holm** under domain-clustered inference on the direction side. The
   L8/L12/L16/L20/L24 entries are directionally consistent across estimators but individually
   uncorrected-significant only.
3. **The probe `d4` is partly saturated** (`saturation_frac` 0.26–0.50), so its margins are
   compressed and its magnitudes should not be compared to the direction's on an absolute scale.
4. **`d3`'s recall = 1.00 is a lexical-identity result** (audit finding #11/#18): it shows the
   diagonal probe is not confusing concept with *harm context*, but it cannot separate
   concept-identity from *token identity*, because the two are perfectly confounded in that design.

---

## Adopting the three reference codebases (answering a direct question from the user)

The user asked whether this sprint uses the Doublespeak code, the CoT-ness/Role-Confusion work and
the Ben-Tov/Geva/Sharif hijacking paper. Honest answer at the time: **two partially, one not at
all.** Full audit in `notes/three_codebase_adoption.md`.

| codebase | before | now |
|---|---|---|
| **Doublespeak** (`ds_common`/`pair_common`) | reused wholesale | unchanged |
| **interp-jailbreak** (2506.12880) | cloned, methodology noted, **code reimplemented** | port planned (P1), see below |
| **Role Confusion** (`third_party/prompt_injection_role_confusion`) | **never opened** | **adopted (P0)** |

The Role-Confusion miss was the bad one: the code was already in this repo and contains exactly the
Userness/CoTness machinery §11 asks for, while I had written role-style prompt wrappers, no probes,
and marked P7.3 "if feasible".

### P0 done — `src/boombness/role_probes.py`

Ported from `experiments/role-analysis/02-train-role-probes.ipynb` cells 18/19/26 and
`utils/role_templates.py`, keeping their design decisions rather than inventing:

- **`SKIP_FIRST_N = 32`** — drop the first 32 tokens of each role segment, because the role tag
  sits at the segment start and without this the probe reads the tag and reports ~100% while
  measuring nothing. Their guard against exactly the failure mode this sprint already hit once.
- **`C = 5e-3`**, L2, optional standardization — from their per-model `config/probe.yaml`.
  Worth noting: **my own probe saturated at the sklearn default `C=1.0`; they had already solved
  that three orders of magnitude away.** Had I read their config first I would not have spent a
  tick rediscovering it.
- **Grouped split by conversation**, never by token.
- **The tagged / untagged / mistagged triad** (their cell 26) — the same content with no tags, with
  its true tags, and wrapped in the *wrong* tag. This is the validity gate that makes a role probe
  mean anything: a probe that learned *role* must follow the TAG, not the content. Verified by
  self-test that all five renderings preserve the content exactly and differ only in markup.
- **Added `render_single_llama3`**, which their repo does not ship (their model set is gpt-oss /
  Qwen3 / GLM / OLMo / Jamba / Apriel / Nemotron), written to match the official Llama-3.1 template.

Two deviations recorded rather than inherited silently: sklearn instead of cuml (not installed, and
at our n the GPU path buys nothing), and **extraction site** — their probes train on
`post_attention_layernorm` output while our patching machinery works on the residual stream, so we
extract there and **their published `C` must be re-swept** rather than assumed.

### Next from the adoption plan
- **P1** `src/boombness/dominance.py` — port the hijacking paper's dominance score onto HF eager
  attention. Notably our port should be *better* than theirs for this use: they materialize the
  per-head value-flow tensor for all layers and all destinations (~28 GB at T=120); we need one
  destination (the final codeword token), which is ~T× cheaper. **Do not install their
  TransformerLens fork.** Pair the ranking with `pair_common.AttentionKnockout` on the same edges.
- **P2** `refusal_dir_adapter.py` — their refusal-direction *selection* is better than ours
  (position×layer candidate bank, KL≤0.1 coherence guard, bidirectional induce check); their
  datasets are not (none of their checkpoints are our models). Their machinery, our data.
- Blocker recorded: `Chain_of_Thought_Hijacking/Hijacking/` contains **no hooks or attention
  capture at all**, so §10.1 edge knockout must come from our `AttentionKnockout` plus the
  interp-jailbreak port, not from that repo.

### 2026-08-16 — Tick 12 (Phase 5 + Phase 2 launched; dominance score ported)

**Jobs:** `760714` full Phase-5 pass (behavioural generation + semantic + comprehension over the
1752-row bank — the input to gate **G2**); `760722` Phase-2 pilot at 8 families × {4,8} demos ×
α∈{0.5,1,2,4} on the **forced-choice** readout (gate **G1**); `760719` dominance self-test.

`760715` (first pilot attempt) **FAILED at launch**: `--query-kind` had a hardcoded `choices=[...]`
that desynced when `semantic_forced_choice` was added two ticks earlier. Now derived from
`prompt_families.QUERY_KINDS`, so the list cannot drift from the generator again. Cheap failure —
argparse rejected it in 65 s — but it is the same *class* as the dosing bug that recurred: a value
restated in a second place instead of read from one.

**P1 of the adoption plan done — `src/boombness/dominance.py`.** The hijacking paper's dominance
score, ported to HF eager attention. Their quantity exactly:

```
Y[l,h,dst,src,:] = A[l,h,dst,src] · (W_O[l,h] @ v[l,h,src])
D_attn = <Y, attn_out[dst]> / ‖attn_out[dst]‖²      sums to 1 over (head, src)
D_dir  = <Y, unit(dir)>                              with dir = d_surface[l]
```

`D_dir[h, src]` answers plan §10.1 directly: **how much of the Boombness arriving at the final
codeword token was supplied by each demonstration token, through which head** — which is the
ranking that tells `AttentionKnockout` which edges are worth cutting, instead of cutting all of
them and reporting that something happened.

**Our port is cheaper than theirs, and not by cutting corners.** They materialize `Y` for all
layers and all destinations — `[n_layer, n_head, T, T, d_model]`, ~28 GB at T=120 on an 8B model.
We need **one** destination (the final codeword occurrence), which removes a factor of T; and for
`D_dir` the `d_model` axis collapses analytically:

```
<Y[h,src], u> = A[h,dst,src] · <v[h,src], W_Oᵀ u>
```

so `wo_dir[h] = W_Oᵀu` is precomputed once per head ([head_dim]) and **no `[T, d_model]` tensor is
ever built**. Two invariants are asserted rather than trusted, mirroring their own checks:
`Σ_{h,src} Y == attn_out[dst]` and `Σ D_attn == 1` — which is also what catches a wrong GQA head
mapping (Llama-3.1-8B: 32 query heads over 8 KV heads, so query head `h` reads KV head `h//4`).
`attn_implementation="eager"` is required, the same constraint `AttentionKnockout` has.

### 2026-08-16 — Tick 13 (two launch failures, both caught by guards; jobs relaunched)

- **760714** (Phase 5, gate G2 input) running well: 1300/1464 rows, 506 behavioural generations
  written so far, 288 comprehension, 0 failures.
- **760722** (Phase 2 pilot) produced **0 rows** — every family rejected by the live position
  assertion. Correct behaviour: I had pointed the pilot at `semantic_forced_choice`, a query kind
  that names *both* words, so donor and recipient target occurrences do not correspond and a
  position-matched transplant is undefined. The generator already marks it
  `occurrence_analysis_safe=False`; `aggressive_patching` simply did not consult that flag. It does
  now, and refuses up front rather than failing 16 times with a cryptic reason.
- **760719** (dominance self-test) died on a device mismatch — captured `v` on cuda, projection on
  cpu. Single-destination arithmetic is now explicitly CPU float32.

Both are cheap, both were caught by guards rather than by producing a wrong number, and both are
the *same class* as the two earlier recurrences: **a fact stated in one place and not consulted in
another** (the hardcoded `choices` list, the `occurrence_analysis_safe` flag, the `gap` dose unit).
That is now three instances, so it is a pattern in this codebase rather than three accidents — the
mitigation is to derive from the source of truth rather than restate, which is what all three fixes
did.

---

## Tick 13b — Phase 5 forward readouts: the central dissociation

`base_20260816_203355_3985444`: 660 behavioural generations + 516 semantic + 288 comprehension
readouts over the bank, **0 failures**. ASR judging is running separately; the forward readouts are
already decisive on their own.

### The semantic readout — what the model SAYS the codeword means

Paired within **60 matched core-2×2 families** (`log p(concept) − log p(codeword)` at the answer
position):

| cell | mean | |
|---|---|---|
| A benign_literal | −14.48 | the codeword read literally |
| C natural_doublespeak | **−1.73** | |
| E concept_in_benign_ctx | +1.98 | |
| B direct_harmful | +7.00 | the concept read directly |

**paired `C−A` = +12.76 ± 0.68 (t = 18.7, n = 60 families)**, against `B−A` = +21.49 — so the
doublespeak prompt carries the codeword **59.4%** of the way from a literal reading to the direct
concept. And it is cleanly **dose-dependent in demonstrations**:

| n_examples | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| paired C−A | +7.56 | +10.76 | +12.95 | +15.71 | **+16.81** |

The controls hold: **`F` benign_remap = −10.89**, close to the literal arm `A` and nowhere near `C`.
So the *structure* of a remapping alone produces almost nothing — the effect is specific to
remapping onto the harmful concept, which is exactly what plan §2.5's control is for.
`D` direct_codeword = +4.11: **stating** the mapping outright beats demonstrating it.

### The comprehension control — the model knows it is a codeword

`log p(coded) − log p(literal)`: A = −4.99 (**1.7%** say "coded"), **C = +0.70 (68.3% say
"coded")**, B = −3.05 (20%). So in the doublespeak arm the model explicitly reports the word is
being used as a code, two thirds of the time. Comprehension is intact, which is what makes any
later "intervention reduced ASR" claim interpretable at all (§2.6).

### THE DISSOCIATION — this is the sprint's main finding so far

| quantity | doublespeak effect | dose-response in demonstrations |
|---|---|---|
| **what the model SAYS the word means** (semantic log-odds) | **+59% of the way to direct**, t=18.7 | **monotonically increasing**: +7.6 → +16.8 |
| **the token's representation along the concept axis** (`d_surface`) | **~3–5%**, and only L4/L31 survive correction | **mid-layers move the WRONG way**: L20 goes −0.002 → −0.051 as demos increase |

The plan's hypothesis — *"benign surface tokens acquire a hidden representation that is increasingly
concept-like"* — is **true as a claim about what the model computes, and false as a claim about the
token's own representation moving along the concept-identity axis.** More demonstrations make the
model report the codeword as the concept far more strongly, while pushing the token's mid-layer
representation *further from* the concept direction.

**Direct consequence for plan §12:** a GCG objective that maximizes `⟨h_final_codeword, d_surface⟩`
would be optimizing the quantity that does *not* track the behaviour. The semantic log-odds — or
whatever mediates it — is the candidate worth optimizing, and identifying that mediator is the
obvious next experiment.

### `dominance.py` verified (adoption plan P1)

Self-test on Llama-3.1-8B: `Σ_{head,src} D_attn = 1.000000` at L8 and L18, shape `[32 heads, T]`.
The value-flow decomposition reconstructs the attention output exactly, which confirms the GQA head
mapping (32 query heads over 8 KV heads, `h//4`) and the `o_proj` per-head slicing are right.

---

## ✅ GATE G1 — answered (pilot `pilot_20260816_210506_1142800`, 2368 rows, 0 failures)

8 families × {4,8} demos, forced readout = semantic log-odds. Self-swap is an **exact** no-op
(`Δ = 0.00e+00`) in both pairs, so the machinery is sound and a null would be a real null.

`harm_ctx` (recipient = doublespeak, donor = direct). Baseline −1.72, donor ceiling +6.37,
**span = 8.09**. Effect expressed as % of that span:

| intervention | semantic log-odds | % of span |
|---|---|---|
| **transplant, QUERY token only, L8** | −7.84 | **−75.6%** |
| transplant, query only, L8–21 | −8.25 | **−80.7%** |
| **transplant, DEMONSTRATIONS only, L8** | +4.00 | **+70.8%** |
| **transplant, demonstrations only, L18** | +5.07 | **+83.9%** |
| transplant, all positions, all layers | +6.37 | +100.0% |
| add `d_surface` α=1 (L8–21, query) | +2.85 | +56.5% |
| add **random** α=1 | −3.95 | −27.5% |
| add **orthogonal** α=1 | −3.95 | −27.5% |

### The answer, and it inverts the representation-level reading

**§5.4 Q6 — which token positions matter? THE DEMONSTRATIONS, not the query token.**
Transplanting the direct prompt's concept representation into the **demonstration** positions moves
the semantic readout **71–84% of the way** to the direct-prompt ceiling. Transplanting it into the
**query token itself moves the readout ~76–81% the WRONG WAY** — it destroys the doublespeak
reading rather than strengthening it.

That is the exact opposite of what the representation-level result said at tick 9, where
`demos_only` did nothing to `⟨h_query, d_surface⟩` and `query_only` did everything. Both are true
and consistent: overwriting the query token's own state removes the *thing being asked about*, while
the meaning the model reports is computed by **reading the demonstrations**. The codeword's meaning
is not stored in the codeword token; it is retrieved from the demonstration block at answer time.

**§5.4 Q7 — which layers?** A single layer suffices on the demo positions: L8 alone gives +70.8%,
L18 alone +83.9%. No wide band is needed.

**§5.4 Q1 — can we force it?** Yes, and controls pass: norm-matched **random** and **orthogonal**
directions at the same dose move the readout −27.5% (they *degrade* it), against +56.5% for
`d_surface`, so the additive effect is axis-specific rather than generic perturbation. The additive
dose-response peaks at α=1 (+56.5%) and *declines* at α=2 and α=4 (+48%, +38%) — over-driving the
direction damages the representation, which is itself an argument against a naive "maximize the
projection" GCG objective.

**Verdict: G1 = PASS, with the mechanism relocated.** We can control the behaviour, but the lever is
the demonstration block, not the codeword token's representation. Combined with the tick-13b
dissociation, the sprint's working model is now: *the doublespeak effect is a retrieval phenomenon
over the demonstrations, not a rewriting of the codeword token.*

**Caveat:** n=8 families per cell in this pilot, so the SEs are ±0.5–1.6 log-odds. The direction and
sign of every effect above is far larger than that, but the exact percentages should be re-measured
at the plan's ≥20-per-condition before they are quoted as final.

### 2026-08-16 — Tick 14 (Phase 6 built, motivated by G1)

**`src/boombness/surgical_knockout.py`** (plan §10.1/§10.2), written *because* of the G1 result
rather than as a checklist item. G1 says the doublespeak reading is driven by the demonstration
positions and that the codeword's meaning is retrieved from them at answer time. If that is right,
cutting the attention edges from the final codeword token to the demonstration tokens should
collapse the semantic readout, and cutting the same number of other edges should not.

It composes the two pieces already built and verified:
- **`dominance.py`** ranks the edges — `D_dir[h, src]` is how much Boombness arrived at the final
  codeword token from source `src` through head `h`. This is what makes the cut *surgical* instead
  of "ablate the demo block and report that something happened".
- **`pair_common.AttentionKnockout`** cuts specific (query → key) edges per layer and head. It is a
  silent no-op under SDPA, so the loader forces `attn_implementation="eager"`.

Seven arms, all cutting the **same number** of edges except the floor and ceiling, with the count
recorded per row so equality can be checked rather than assumed:

| arm | tests |
|---|---|
| `topk_demo` | the hypothesis — the highest-|D_dir| demonstration edges |
| `bottomk_demo` | is the *ranking* real, or would any demo edges do? |
| `random_demo` | is it *these* edges? |
| `random_nondemo` | is it the demonstrations at all? |
| `same_head_random` | head or position — same heads, random positions |
| `all_demo` / `none` | ceiling and floor |

Smoke submitted as **760740**. ASR judging for G2 is at 597/660.

---

## ✅ GATE G2 — answered. The representation Boombness does NOT predict ASR; the semantic one does.

ASR from `judge/base_20260816_210948_3024689`: 660 generations, **null_frac = 0.0000**, StrongReject
rubric, binary at 0.5, continuous score persisted.

### The attack is real, and it works by removing refusal

| condition | n | ASR@0.5 | mean score | **refusal rate** |
|---|---|---|---|---|
| `direct_harmful` (B) | 72 | 0.042 | 0.042 | **0.958** |
| `natural_doublespeak` (C) | 270 | **0.219** | 0.188 | **0.074** |
| `direct_codeword` (D) | 36 | **0.583** | 0.601 | **0.000** |
| `benign_literal` (A) | 174 | 0.029 | 0.019 | 0.086 |
| `benign_remap` (F) | 36 | 0.028 | 0.017 | 0.389 |
| `concept_in_benign_ctx` (E) | 72 | 0.014 | 0.017 | 0.931 |

Doublespeak gives **5.2× the direct-request ASR**, and *stating* the mapping outright gives **14×**.
The mechanism is visible in the last column: refusal collapses from **96% → 7%**. The controls sit at
floor (1.4–2.9%), including `benign_remap`, so it is not the remapping structure.

### The decisive comparison (plan §9 Q2/Q5/Q7)

Spearman against the continuous StrongReject score. **Within the doublespeak arm** is the meaningful
column — across conditions the correlation is dominated by condition differences, not by Boombness.

| predictor | all conditions | **within doublespeak (n=198)** |
|---|---|---|
| **semantic log-odds** | +0.269 (p=5.6e-10) | **+0.418 (p=9.2e-10)** |
| `d_surface` cos @ L4 | −0.130 | +0.097 (p=0.17) — null |
| `d_surface` cos @ L8 | −0.161 | +0.050 (p=0.48) — null |
| `d_surface` cos @ L12 | −0.205 | −0.035 (p=0.62) — null |
| `d_surface` cos @ L20 | −0.182 | +0.057 (p=0.42) — null |
| `d_surface` cos @ L31 | −0.014 | +0.226 (p=1.4e-3) — weak |

**Incremental value:** within doublespeak, R² for semantic alone = 0.1914; adding `d_surface@L31`
gives 0.1953 — **Δ = +0.004**. The representation metric contributes essentially nothing beyond the
semantic one.

### What this means for the plan's core proposal

The sprint's §0 hypothesis was that the codeword acquires an increasingly concept-like *hidden
representation*, that this predicts ASR, and that it can therefore be turned into a GCG objective.
The first clause is only marginally true (§tick-13b: ~3–5% movement, and mid-layers move the wrong
way with more demonstrations). **The second clause is false**: at the layers where the plan would
site an objective (L8–L20, the write/carry band), `⟨h_final_codeword, d_surface⟩` has **no
detectable relationship to attack success** (|ρ| ≤ 0.10, all p > 0.15).

So **a GCG objective maximizing the representation Boombness would be optimizing a quantity that
does not track the behaviour** — which is exactly the §12 gate the plan asked us to check before
building the optimizer. The semantic log-odds *does* track it (ρ = 0.42), and the G1 result says the
lever for that quantity is the **demonstration block**, not the codeword token.

**G2 verdict: the plan's proposed objective is a documented NEGATIVE. A better-supported objective
exists (semantic log-odds / the demonstration-retrieval pathway) and is the one worth optimizing.**

Not yet measured: refusalness per prompt, so §9 Q6/Q7 ("does Boombness beat/add-to refusalness")
remain open. Given refusal moves 96%→7% between arms, refusalness is likely the dominant term and
that comparison is the next thing to run.

### 2026-08-16 — Tick 15 (the §10 null was a dead intervention — caught by the positive control)

The knockout smoke returned deltas of ≤0.12 log-odds with three arms at *exactly* 0.000, which is
the signature of an intervention that is not firing rather than one that has no effect. So I added a
**positive control** — block every pre-query key in every head at the chosen layers — and it failed:

| arm | Δ semantic log-odds | edges cut |
|---|---|---|
| `topk_demo` | +0.044 | 16 |
| `all_demo` | +0.117 | 256 |
| **`positive_control`** | **−0.086** | **7392** |

Leaving the final token attending only to itself, at two layers, cannot move the readout by 0.086.
**The knockout is not reaching the computation**, and every §10 arm is void.

This is the single most valuable thing the positive control has done all sprint: without it I would
have written "cutting the demonstration edges has no effect on the semantic readout", which — given
G1 says the demonstrations are the causal lever — would have been a *striking* and completely false
result. It would have fitted the retracted representation story neatly, which is exactly what makes
it dangerous.

`diagnose_knockout.py` (job 760757) settles it by measuring the attention weights directly with and
without a total mask-out. **If the weights are unchanged, the defect is in
`pair_common.AttentionKnockout` under transformers 5.12 and affects any prior result in this
repository that used it** — not only this sprint. That possibility is flagged now rather than after
the check, because it changes who needs to know.

**Meanwhile, refusalness (§9 Q6/Q7) is the next measurement**, and it is the one that decides
between plan outcome **A** (Boombness is the story) and outcome **C** (refusal suppression is the
story, with Boombness a correlate). Given ASR refusal rates of 95.8% → 7.4% → 0.0% across
direct / doublespeak / stated-mapping, outcome C is currently the more likely reading.

### 2026-08-16 — Tick 15b (CORRECTION: the knockout does fire; my impossibility argument was wrong)

`diagnose_knockout.py` (job 760757) measured it directly and **refutes the tick-15 conclusion**:

```
attention mass on keys < dst, clean   : 0.945386   self: 0.054614
attention mass on keys < dst, knocked : 0.000000   self: 1.000000
max |Δ attention weight| = 9.97e-01      max |Δ final logit| = 1.16e+00
```

`AttentionKnockout` fires exactly as specified. **My reasoning was the error**, not the code: I
argued that a 0.086 log-odds change was "physically impossible" after cutting 7392 edges. But one
layer's attention at one position moves the final logits by only ~1.16, and the semantic readout is
a **log-odds ratio** — both terms shift together, so the difference can move much less than either
term. I asserted an impossibility from intuition instead of measuring the magnitude first.

**The warning that prior repo results using `AttentionKnockout` might be void is withdrawn.** It was
wrong and it was the kind of claim that should not have been made before the check it was waiting
on — I flagged it early on the grounds that "it changes who needs to know", which cuts both ways.

One real difference remains: the diagnostic used a **single all-head** knockout, whereas
`surgical_knockout` **stacks one context manager per head** (32 per layer) because it cuts a
per-(head, src) edge set. Those must be equivalent when the per-head sets cover all heads. Job
760762 tests it. Until then the §10 arms are provisional — but the likely reading now is that the
§10 null is **genuine**, which is itself informative: attention-edge cuts at L8/L18 do not move the
semantic readout even though transplanting the demonstration *states* moves it 71–84%.

If that holds, it says the demonstration influence is **not** carried by the attention edges from
the final codeword token at those layers — the retrieval happens somewhere else, or earlier, or is
distributed enough that cutting 16 edges per layer cannot touch it.

---

## §10 result — the demonstration influence is INDIRECT (machinery fully verified)

The composition check closes the loop: 32 stacked per-head knockouts are **bit-identical** to one
all-head knockout (`max|Δ attention| = 0.000000e+00`, `max|Δ logit| = 0.000000e+00`). Combined with
the total-mask-out test (attention mass 0.945 → 0.000), **the §10 machinery is verified end to end**
and the null is a real null.

### The finding

Both interventions target **the same positions** — the demonstration codeword occurrences
(`last[:-1]`) — at the same layers, on the same readout:

| intervention at the demo codeword positions | effect on semantic log-odds |
|---|---|
| **replace the STATE** there (transplant, L8 or L18) | **+71% to +84% of span** |
| **cut the ATTENTION EDGES** from the final codeword token to them (L8, L18) | **≈ 0** (`topk` +0.044, `all_demo` +0.117 with all 256 edges cut) |

So the demonstration codeword states matter enormously, but **not through direct attention from the
final codeword token to them at these layers**. Cutting *every* query→demo edge at L8 and L18 does
essentially nothing.

The reading is that the influence is **indirect / multi-hop**: perturbing the state at demo position
`p` changes everything causally downstream of `p` — other demonstration tokens, intervening text,
and the query position at later layers — whereas cutting the query→`p` edge blocks only the direct
one-hop path. A one-hop attention story for doublespeak retrieval is therefore **not supported**.

**Caveats, explicitly:** only L8 and L18 were tested, and only edges to the demo *codeword* tokens
(not the whole demonstration block). A wider layer sweep and whole-block edge cuts are the obvious
follow-ups, and `dominance.py` already provides the ranking to target them.

This also revises the G1 reading slightly. G1 established the demonstrations are the causal lever;
§10 now says that lever is **not** a direct attention pathway into the codeword token. Together with
G2 (the representation Boombness does not predict ASR), the emerging picture is that the doublespeak
effect is neither "the codeword token becomes concept-like" nor "the query token reads the demos in
one hop".

### 2026-08-16 — Tick 16 (second 4-hourly audit; refusalness measurement launched)

**`refusalness.py` submitted (job 760773)** — plan §9 Q6/Q7, and the measurement that decides the
sprint's §18 outcome label:

- **outcome A** — Boombness is the story;
- **outcome C** — refusal suppression is the story and Boombness is a correlate of it.

It measures `<h[final prompt token, L], unit(v_refusal[L])>` at L12/14/16/18/20 using the **house**
refusal directions (`stage_gcg_full/refusal_direction_llama_L*.pt`), so the numbers are comparable
to every previous refusal result in this repo rather than to a private re-derivation.

The design choice that matters: refusalness is measured **on the prompt, before generation**. Using
the *observed* refusal in the output would be near-circular — refusal and ASR are close to
complementary by construction, so "refusal predicts ASR" would be a tautology rather than a finding.

**Second independent audit launched**, pointed squarely at the gate verdicts rather than the code:

| auditor | brief |
|---|---|
| `g2-asr` | reproduce rho=+0.418 and the `d_surface` nulls; check the family_id join (stripping the query-kind component - could it collide two families?); redo with **domain-level aggregation** as the hijacking paper does; test whether the `d_surface` null is **range restriction** rather than absence of relationship; and whether "a GCG objective on `d_surface` would optimize the wrong quantity" overreaches from a correlational null |
| `g1-g3-power` | G1 rests on **n=8 families**, G3 on **n=2 prompts** - compute real intervals; G1's percentages share a noisy denominator (the span, estimated from the same 8), so propagate that; is G3's "one-hop attention not supported" broader than a 2-layer, codeword-positions-only design supports? |
| `new-code` | `dominance.py` GQA mapping independent of its own self-test; whether `abs()` in the top-k ranking conflates positive and negative flow; whether `refusalness.py` is exposed to the transformers 5.12 last-layer tie; what else was silently inherited from the role-confusion port |
| `consistency` | is anything in the **retracted** sections still being relied on downstream? spot-check >=10 quoted numbers against their cited runs; is any phase marked DONE on invalidated evidence? |

Two of those I consider genuine risks to the current verdicts rather than box-ticking: **range
restriction** could manufacture the G2 null, and **n=2** cannot distinguish G3's null from a large
effect.

---

## ⛔⛔ RETRACTION #2 — G2 was BACKWARDS. The representation Boombness DOES predict ASR.

The tick-16 audit (44 agents, 40 candidates, **30 confirmed**) found that the G2 table read the
predictor **off the wrong prompt**. Recomputed with the committed, reproducible
`src/boombness/analyze_g2.py`:

```
python src/boombness/analyze_g2.py \
  --judge   outputs/boombness/judge/base_20260816_210948_3024689 \
  --extract outputs/boombness/extract_boombness/full_20260816_185942_1008673 \
  --score   outputs/boombness/score_behavior/base_20260816_203355_3985444
```

`arm=natural_doublespeak`: **270 judged prompts, 270 with a representation (100% coverage)**,
234 analysed after excluding zero-demo prompts. Spearman vs continuous StrongReject, Holm over
predictors:

| predictor | ρ | p | Holm |
|---|---|---|---|
| **`d_surface` L8 proj** | **+0.342** | 8.0e-08 | ✓ |
| `d_surface` L12 proj | +0.307 | 1.7e-06 | ✓ |
| `d_surface` L11 cos | +0.305 | 1.9e-06 | ✓ |
| `d_surface` L31 cos | +0.305 | 2.0e-06 | ✓ |
| `d_surface` L8 cos | +0.292 | 5.4e-06 | ✓ |
| logit lens L31 | +0.279 | 1.5e-05 | ✓ |
| **`semantic_logodds`** (n=162, *different* prompt) | **+0.249** | 1.4e-03 | ✓ |

**21 predictors survive Holm. The representation Boombness at L8 predicts ASR BETTER than the
semantic readout does (+0.342 vs +0.249).** My published verdict — *"the representation Boombness
does not predict ASR; the plan's proposed objective is a documented negative"* — was **exactly
backwards.**

### What went wrong, and it is the same mistake as the first retraction

The join stripped `query_kind` from `family_id` to match arms. That is a sound *key*, but it pulled
`d_surface` from the **`semantic_one_word` prompt** while ASR came from the **`behavioral` prompt** —
two different prompts with different final queries. The quantity that bears on a GCG objective is
the representation on the **attack** prompt. `analyze_g2.py` now joins on `prompt_id` directly and
**refuses to run** if the representation rows come from any query kind other than the judged one.

Three further confirmed defects, all in the same ad-hoc analysis:
1. **72 of 270 doublespeak rows were silently dropped** by that join — and not at random: the
   dropped set was entirely `strength=none/consistent/near/plain`, with ASR 0.224 vs 0.176 and
   refusal 0.000 vs 0.101. **This is the identical failure mode — an unreported restriction — that
   forced retraction #1.** Coverage is now printed on every run and is 100%.
2. **36 of the 198 rows had `n_examples=0`** — no demonstrations, so no codeword mapping, so not
   doublespeak prompts at all. That stratum alone carries ρ=+0.717 at L31. Now excluded by default
   (`--min-examples 1`) and reported separately.
3. **Three of five coefficients did not reproduce**, and *nothing in the repo could regenerate the
   table* — it lived in a shell heredoc. That is a direct violation of the plan's §2.1
   reproducibility contract, which I wrote the `RunDir` machinery to enforce and then bypassed for
   the single most important table in the sprint.

### Corrected verdicts

- **G2 = the representation Boombness DOES predict ASR** (ρ≈+0.29–0.34 at L8–L12, Holm-significant,
  100% coverage). The semantic readout also predicts it (+0.249) but *less well*, and on a different
  prompt.
- **G4 = the plan's proposed GCG objective is NOT a documented negative.** It is viable and now
  worth testing. My "documented negative" was an artifact.
- The **tick-13b dissociation** claim (semantic moves 59%, representation only 3–5%) still stands as
  a statement about *effect sizes*, but its interpretation — "the representation is not what tracks
  behaviour" — is withdrawn.

---

## §9 Q6/Q7 answered — Boombness dominates refusalness *within* the attack arm (outcome A, with a C-shaped caveat)

`refusalness.py` (job 760773), house refusal directions, measured on the **prompt before
generation**. Mediation computed by the committed `analyze_g2.py --refusalness …`, so every number
below is regenerable from one command.

### Between arms, refusal is the whole story

mean refusalness (L18 projection) by condition:

| condition | refusalness |
|---|---|
| `direct_harmful` | **+7.30** |
| `concept_in_benign_ctx` | +6.29 |
| `benign_remap` | +0.67 |
| `direct_codeword` | +0.10 |
| **`natural_doublespeak`** | **+0.04** |
| `benign_literal` | −0.15 |

A doublespeak prompt is, to the refusal direction, **indistinguishable from a benign one** (+0.04 vs
−0.15) while the matched direct request sits at +7.30. That is what the ASR table's 95.8% → 7.4%
refusal collapse looks like in representation space.

### Within the attack arm, refusalness explains almost nothing and ⛔ RETRACTED (C2) — see the correction below. ~~Boombness explains 14× more~~

n = 234 doublespeak prompts, `n_examples ≥ 1`, 100% coverage. R² against the continuous
StrongReject score:

| model | R² |
|---|---|
| refusalness (L18) alone | **0.0032** |
| `d_surface` L12 proj alone | **0.1411** |
| both | 0.1416 |
| **Boombness adds over refusalness** | **+0.1384** |
| **refusalness adds over Boombness** | **+0.0005** |

Same picture at every refusal layer tested (L12/16/18/20): refusalness-only R² ranges 0.0013–0.0386,
Boombness-only 0.115–0.141, and refusalness contributes ≤+0.008 on top of Boombness.

**Plan §9 Q6 — does Boombness predict ASR better than refusalness? ⛔ RETRACTED (C2): ~~YES, by ~40×~~. The real figure is ~3.7× (R² 0.141 vs 0.039), and it carries a footing caveat — the two predictors are read at different token positions.** In explained
variance. **Q7 — does it add beyond refusalness? YES (+0.138); the converse is +0.0005.**

### The two-level reading, which is what I think is actually true

- **Between arms:** the attack works by *collapsing refusal* — 7.30 → 0.04. Refusal suppression is
  why doublespeak succeeds where a direct request fails.
- **Within the attack:** *which* doublespeak prompts succeed is predicted by **Boombness**
  (R²=0.14), not by residual refusalness (R²=0.003).

So the plan's §18 label is **A** — Boombness is the story — **for the within-attack variation**,
while the between-arm effect is **C**-shaped (refusal suppression). Those are compatible, and
collapsing them into one label would lose the finding.

### Caveats, stated up front this time
1. **Correlational.** No steering experiment yet. §12's objective test would settle direction.
2. **Within-arm only**, one model (Llama-3.1-8B), one concept pair (carrot↔bomb).
3. R² ≈ 0.14 means Boombness explains ~14% of ASR variance — real and dominant relative to
   refusalness, but most of the variance is still unexplained.

---

## Corrections to G1 and G3 (now produced by the committed `analyze_g1_g3.py`)

Same lesson as retraction #2: G1 and G3 were also computed ad hoc, so they were regenerated by a
script with the statistics the audit said were missing.

### G1 — direction robust, **magnitude was over-precise**

The percentages are ratios whose denominator (the baseline→ceiling span) is itself estimated from
the same n=8 families. Propagating that (delta method) gives:

| arm (harm_ctx) | mean | % of span | **95% CI on the %** |
|---|---|---|---|
| transplant demos_only L18 | +5.07 | +83.9% | **[+33%, +135%]** |
| transplant demos_only L8 | +4.00 | +70.8% | **[+23%, +119%]** |
| transplant query_only L8 | −7.84 | −75.6% | **[−127%, −24%]** |

**The sign and the qualitative claim survive** — transplanting the demonstrations moves the readout
strongly toward the donor, transplanting the query token moves it strongly the other way, and the
self-swap is an exact no-op (`max|Δ| = 0.00e+00`). **The precision does not.** Quoting "+71% to
+84%" implied a tightness that n=8 cannot support; the honest statement is "large and positive, CI
roughly +23% to +135%". G1's verdict stands; its numbers are restated with intervals.

### G3 — **retracted as a null. The positive control established no dynamic range.**

The audit's point is correct and is now enforced in code:

```
positive control Δ = -0.086 ; largest other arm Δ = +0.117
** NO DYNAMIC RANGE ESTABLISHED **
```

The positive control was supposed to prove the readout *can* move under an attention intervention.
It moved the readout **less than `all_demo`, the arm it was meant to validate**. So the §10 null is
**uninterpretable**: I never showed the readout is movable by attention masking at all, which means
"cutting the demo edges does nothing" carries no information.

`analyze_g1_g3.py` now refuses to report a null unless the positive control dominates the arms by
≥3×, and prints the refusal.

**What I got wrong, twice, in the same place:** at tick 15 I called this null "a dead intervention",
then at tick 15b corrected to "the machinery fires, so the null is genuine". Both were premature.
The machinery *does* fire (attention mass 0.945→0.000) — but firing is not the same as the
*readout* being responsive to it. A verified intervention plus an unverified readout is still an
uninterpretable null.

**A real dynamic-range control is needed** — e.g. deleting the demonstrations from the prompt
outright, which must move the readout enormously — before §10 can conclude anything. Until then G3
is **UNRESOLVED**, not a null.

### 2026-08-17 — Tick 19 (fixing G3's missing dynamic range; steering still generating)

Steering arms 760798/799/800 still generating (660 behavioural prompts × 192 tokens each, ×3 arms).

**Two dynamic-range controls added to `surgical_knockout.py`** (job 760806), because the original
`positive_control` did not establish one:

| new arm | what it bounds |
|---|---|
| `all_layers_demo` | cut query→demo edges at **every** layer, not just the chosen two. If the demonstration influence is distributed over depth, a 2-layer cut can do nothing while an all-layer cut does a lot — and **the first design could not see that distinction at all**, which is the actual reason the §10 null was uninterpretable. |
| `no_demo_text` | evaluate the same query with the **demonstration block deleted**. This is the true ceiling: what "the demonstrations are not there" actually means, in text space, with no attention machinery involved. |

The second is the one that matters most. If deleting the demonstrations outright does not move the
semantic readout, then the readout is not measuring the demonstrations' influence and **nothing in
§10 can be interpreted** — including the arms I already reported. If it moves the readout a lot,
then a 2-layer attention cut doing nothing becomes a real and interesting localization result rather
than an artifact.

Sample also raised from 2 to 6 families, since n=2 was the other thing the audit flagged about G3.

---

## ✅ GATE G3 — resolved. The demonstrations' influence is NOT carried by attention to the codeword tokens.

`dynrange_20260817_000454_3064437`, 6 families, 60 rows, 0 failures. **Dynamic range is now
established**, so the arms are interpretable for the first time:

| arm | Δ semantic log-odds | edges cut | what it is |
|---|---|---|---|
| **`no_demo_text`** | **−11.509** | (text deleted) | **the true ceiling** — the demonstrations removed |
| `positive_control` | −1.135 | 7264 | all pre-query keys, 2 layers |
| **`all_layers_demo`** | **−0.784** | 4096 | **query→demo-codeword edges at ALL 32 layers** |
| `all_demo` | −0.093 | 256 | query→demo-codeword edges, 2 layers |
| `topk_demo` | −0.025 | 16 | |
| `random_demo` / `same_head_random` / `random_nondemo` / `bottomk_demo` | ≈0 | 16 | controls |

### The finding

Deleting the demonstration text moves the readout by **−11.5 log-odds**. Cutting **every** attention
edge from the final codeword token to **every** demonstration codeword token, at **every layer**,
moves it by **−0.78** — about **7% of the ceiling**.

**So ~93% of the demonstrations' influence on what the model thinks the codeword means does not flow
through attention from the query codeword to the demonstration codewords, at any depth.**

That is a much stronger statement than the retracted 2-layer version, and it now has the control to
support it. The natural mechanistic reading is that the mapping is taught by the **predicates**, not
by the repeated codeword tokens: *"A carrot exploded near the bridge"* teaches `carrot = bomb`
through *exploded*, not through *carrot*. The codeword occurrences in the demos are the least
informative tokens in them.

**Obvious next experiment**, now well-posed: cut attention to the **whole demonstration block**
(and separately to the harm predicates) rather than only to the codeword occurrences. `dominance.py`
already ranks arbitrary source positions, so this is a config change, not new machinery.

### Gate history, kept because the process matters more than the answer

G3 went null (uninterpretable) → "dead intervention" (wrong) → "genuine null" (premature) →
**resolved** once a control with real dynamic range existed. The `no_demo_text` arm is four lines of
code and it was the difference between an uninterpretable number and a result. It should have been
in the first version of the module, and the reason it was not is that I designed the controls to
distinguish *between hypotheses* and forgot to include one that establishes the *measurement works
at all*.

### 2026-08-17 — Tick 20 (the predicate hypothesis is now a running experiment)

G3 said cutting every query→demo-**codeword** edge at every layer recovers only ~7% of the effect of
deleting the demonstrations, which points at the **predicates** carrying the mapping. That is now a
config flag rather than a hypothesis in prose:

`surgical_knockout.py --demo-scope {codeword,block}` — `block` treats **every token of the
demonstration block** as a demonstration source, located by character offset of the recorded
`demo_block` inside the templated prompt (so it cannot drift from the generator's own notion of what
the demonstrations are). Every existing arm and control then runs unchanged on the wider scope.

Job **760814** runs `--demo-scope block`. The prediction the G3 result makes is explicit and
falsifiable:

- if the mapping is carried by the predicates, `all_layers_demo` under `block` scope should recover a
  **large** fraction of the `no_demo_text` ceiling (−11.5), versus the ~7% the codeword scope managed;
- if it recovers little there too, then the influence is not carried by attention from the query at
  all, and something other than a retrieval-by-attention account is needed.

Steering arms 760798/760799 still generating (the α=1 and α=2 `d_surface` arms); the norm-matched
random control 760800 has finished with 660 generations and 0 failures.

---

## ⛔⛔⛔ RETRACTION #3 — §10 cut edges into the wrong destination

One tick after recording G3 as resolved, a tick-16 audit finding I had not yet worked through turned
out to be fatal to all of §10, including the resolution itself.

**The knockout blocked attention edges arriving at `dst` = the final CODEWORD occurrence. The
readout is the next-token distribution at the LAST token.** Measured on every prompt in the run,
those are **9 tokens apart**:

```
dst=104  seq_len=114  last_index=113   gap = 9
dst=109  seq_len=119  last_index=118   gap = 9      (all 6 prompts identical)
```

So the intervention and the measurement were about **different tokens**. Blocking what arrives at
the codeword can only reach the readout indirectly, through nine intervening positions — which is
exactly why every attention arm read ≈0 while `no_demo_text` (which deletes the text and therefore
affects everything) moved the readout by −11.5.

**Everything I concluded from §10 is withdrawn**, including "~93% of the demonstrations' influence
does not flow through attention to the codeword tokens" and the predicate hypothesis built on it.
That inference was drawn from a comparison between an intervention on the wrong token and a text
deletion, which is not a comparison at all.

A second defect from the same audit, fixed alongside: the **positive control was blocking the
destination's own self-edge**, so the entire softmax row went `-inf` and the row became uniform —
a degenerate perturbation, not "attend only to yourself". That is very likely why the positive
control moved the readout *less* than `all_demo` and why it established no dynamic range.

Fixes: `--dst {readout,codeword,both}` (default `readout`), self-edges excluded from the positive
control, `--demo-scope block` retained. Job 760814 cancelled mid-run; **760816** runs
`--dst both --demo-scope block`.

### The pattern, stated plainly

This is the third retraction, and the third time the same category of error has done the damage:
**the measured quantity and the manipulated quantity were not the same thing.**

| # | what was manipulated / measured | what should have been |
|---|---|---|
| 1 | pooled over query kinds without saying so | report per query kind |
| 2 | `d_surface` read off the *semantic* prompt, ASR from the *behavioural* prompt | same prompt |
| 3 | edges cut into the *codeword* token, readout at the *last* token | same token |

Each time the code ran, produced plausible numbers, and passed its own internal checks. The
defence that works is not more care — it is a **positive control that ties the manipulation to the
measurement**, which is what `no_demo_text` did for the readout and what `--dst readout` now does
for the intervention.

---

## ✅ GATE G3 — resolved properly. The retrieval IS attention-carried, and it is DISTRIBUTED OVER DEPTH.

`dstfix_20260817_003501_3067690` — `--dst both --demo-scope block`, 6 families, 0 failures. The
destination now matches the readout and the demonstration scope is the whole block.

| arm | Δ semantic log-odds | edges cut | % of ceiling |
|---|---|---|---|
| **`no_demo_text`** | **−11.509** | (text deleted) | 100% (the ceiling) |
| **`all_layers_demo`** | **−9.708** | 56 832 | **84%** |
| `positive_control` | +3.534 | 7 200 | (large, opposite sign) |
| `all_demo` (2 layers) | −0.008 | 3 552 | **0.1%** |
| `topk_demo` / `random_demo` / `bottomk_demo` / `same_head_random` / `random_nondemo` | ≈0 | 16 | ≈0 |

### The finding, and it is the opposite of what I retracted

Cutting attention from the query to the **whole demonstration block at every layer** recovers
**84% of the effect of deleting the demonstrations outright**. The influence *is* attention-carried.

But cutting the same edges at **two layers** (L8 and L18) recovers **0.1%** — 3552 edges, no effect.
And every 16-edge arm is at zero.

**So the retrieval is distributed over depth and highly redundant.** No small set of layers or edges
carries it; removing 2 of 32 layers changes nothing because the remaining 30 suffice. That is why
every localized knockout in this sprint read zero, and why the earlier "attention doesn't carry it"
conclusion was exactly backwards — it was measuring a redundant pathway one slice at a time.

This also retires the predicate hypothesis in its earlier form: the effect appears at **block**
scope, not at codeword scope, so it is the demonstration *content* that matters — but the mechanism
is distributed retrieval, not a sparse circuit.

### Why this is now trustworthy where the previous two versions were not

1. **Dynamic range established** — `no_demo_text` = −11.5 and `positive_control` = +3.5, both far
   larger than any test arm, so a zero in a test arm is informative.
2. **Destination matches the readout** (`--dst both`), the defect that voided the previous run.
3. **Controls at zero** — random, bottom-k, non-demo and same-head-random all ≈0 at matched edge
   counts, so the effect is not "cutting lots of edges does something".
4. **Regenerated by a committed script** (`analyze_g1_g3.py`), not a heredoc.

### Remaining limitations, stated
- **n = 6 families.** The gap between −9.708 and −0.008 is far larger than the SEs (0.898, 0.451),
  but the percentages should be re-measured at the plan's ≥20 per condition.
- `--dst both` cuts into the codeword *and* the readout position, so this run cannot separate their
  contributions. A `--dst readout` arm would isolate it and is the obvious next run.
- The layer sweep is all-or-two. Where between 2 and 32 layers the effect appears — and whether it
  is smoothly redundant or has a threshold — is unmeasured and is the interesting follow-up.

---

## G4 steering — a spurious 3.5× ASR result, caught BEFORE it was reported

The first steering run looked like the result the whole sprint was aiming at:

| arm | ASR@0.5 | vs baseline |
|---|---|---|
| baseline (no intervention) | 0.219 | — |
| **`d_surface` @ L8, α=1 gap** | **0.759** | **3.5×** |
| `d_surface` @ L8, α=2 gap | 0.000 | — |
| norm-matched random, α=1 | 0.000 | — |

Read naively: *steering the Boombness axis causally drives the attack, and the matched random
control does nothing.* That is precisely the §12 finding the plan hoped for.

**It is an artifact.** Structural degeneracy statistics on the same generations:

| arm | uniq-word ratio | 3-gram repeat | top-word frac | truncated |
|---|---|---|---|---|
| baseline | 0.741 | 0.017 | 0.101 | 37% |
| **steer α=1** | **0.302** | **0.551** | 0.139 | **100%** |
| steer α=2 | 0.051 | 0.848 | 0.651 | 100% |
| random α=1 | 0.466 | 0.271 | 0.120 | 72% |

Healthy English sits near 0.55–0.75 unique-word ratio with <0.15 trigram repetition. **The α=1 arm
repeats 55% of its trigrams and never emits EOS.** The α=2 arm is worse — a single word is 65% of
the output. The intervention did not make the model comply; **it broke generation**, and the judge
scored the resulting harmful-adjacent loop as a success.

Plan §2.6 warns against reading a *lowered* ASR as causal understanding when the intervention is
destructive. The same holds with the sign flipped: **a raised ASR from a destroyed model is not a
causal result either** — and it is more seductive, because it confirms the hypothesis.

### `coherence_gate.py` — coherence is now a gate, not a footnote

Committed, with generous thresholds (0.45 uniq / 0.30 trigram / 0.25 top-word / 0.90 truncated).
`--strict` exits non-zero. Applied to the four runs above it passes baseline and random-α=1, and
fails both `d_surface` arms. **No ASR number from an intervention run is reportable until it
passes.**

### Relaunched at doses that might preserve coherence

Jobs **760859** (α=0.10) and **760860** (α=0.25). One gap of `d_surface` is evidently far past the
model's tolerance at L8; the question is whether there is a dose that moves ASR while leaving
generation intact. If there is not, the honest §12 conclusion is that this axis cannot be steered
non-destructively — which is a real finding, and a very different one from "steering works".

**This is the first spurious result in the sprint caught before being written up as a finding
rather than after.** The difference was having a structural check that does not depend on the
number I wanted to see.

### 2026-08-17 — Tick 23 (the dominance verification is now real, and says so)

Job 760858 passed the **reconstruction** check — `sum(Y)` reproduces the module's own `o_proj`
output — so the GQA head mapping (32 query heads over 8 KV heads, `h//4`) and the `o_proj` per-head
slicing are genuinely correct, and the §10 edge ranking rests on something verified.

But the self-test **printed the tautology** as if it were the verdict:

```
L8: D_attn sum=1.000000 (must be 1.0)
selftest OK — the value-flow decomposition reconstructs the attention output, ...
```

A reader of that log would conclude the sum-check is the evidence. It is not — it is 1.0 by
construction for any `Y` at all. The print now leads with the real number and labels the other
explicitly:

```
L8: reconstruction rel.err = ...e-XX  <-- THE CHECK
    (tautological D_attn sum = 1.000000, informative only as a smoke test)
selftest OK — sum(Y) reproduces the module's own o_proj output to ...e-XX relative error ...
    (The D_attn==1 identity proves nothing and is not the basis of this verdict.)
```

Small change, but it is the same class of problem as the rest of this sprint: a *number that looks
like verification* standing in for one. Job **760862** re-runs it.

Low-dose steering (α=0.10, α=0.25) running as **760859** / **760860**; both will go through
`coherence_gate.py` before any ASR from them is read.

---

## §11 role framing — Boombness is FLAT across role styles; the ASR side is underpowered

`analyze_role.py` (committed) over the headline extract + judge runs. `role_style` varies while
demonstration content, domain, demo count and final query are held fixed — the content-constancy
design §11 asks for.

| role_style | n | Boombness L8 | L12 | L31 | n_ASR | mean ASR |
|---|---|---|---|---|---|---|
| plain | 396 | −0.3278 | −0.2954 | −0.2109 | 204 | 0.200 |
| tool | 12 | −0.3202 | −0.3038 | −0.2318 | 6 | 0.146 |
| assistant_like | 12 | −0.3249 | −0.3010 | −0.2169 | 6 | 0.083 |
| cot_like | 12 | −0.3151 | −0.2972 | −0.2215 | 6 | 0.000 |
| system_like_quoted | 12 | −0.3118 | −0.2935 | −0.2093 | 6 | 0.000 |
| user_like | 12 | −0.3265 | −0.3033 | −0.2090 | 6 | 0.000 |

**Boombness is flat.** Across all six role styles the L8 Boombness spans **0.016** (−0.312 to
−0.328) — an order of magnitude smaller than the effects this axis shows elsewhere (the
doublespeak-vs-benign contrast is ~0.29 on the same scale). Role framing does **not** detectably
move the codeword along the concept axis.

Mediation on the rows with both (n=234): R² role-only **0.032**, Boombness-only **0.165**, both
**0.185**. Boombness adds **+0.153** over role; role adds **+0.020** over Boombness.

So on the §11 menu the answer is **(b)/(c)**: role framing does not act through Boombness, and adds
little to ASR prediction beyond it.

### The ASR column must not be read, and I am flagging that rather than burying it

**n_ASR = 6 per non-plain role style.** The apparent ordering (plain 0.200 → tool 0.146 →
assistant 0.083 → cot/system/user 0.000) is six prompts per cell; a single judged prompt moves a
cell by 0.167. Nothing about "cot_like and user_like suppress the attack" is supportable from this,
and the zeros are what six samples of a ~0.2-rate process look like a fair fraction of the time.

The Boombness flatness *is* reasonably supported — n=12 per style, and the between-style spread is
tiny relative to the axis's demonstrated range — but the behavioural claim is not.

**Fix if §11 is to be answered properly:** the `role_style` block in the bank is 6 domains × 1 split
× 2 conditions × 1 demo count = 12 rows per style. It needs the demo-count and split axes opened up
to reach the plan's ≥20 per condition. That is a generator config change, not new machinery.

### 2026-08-17 — Tick 25 (role block given real power; third audit launched, overdue)

**Bank expanded to fix §11's power problem.** The `role_style` block was 6 domains × 1 split ×
2 conditions × 1 demo count = 12 extract rows and only **6 judged** rows per style. Opening the
split and demo-count axes gives **72 behavioural rows per style**:

```
bank: 2352 rows, 240 matched 2x2 families, 0 alignment violations,
      0 token-alignment violations, benign_remap collapse 0,
      bank_content_sha16 7002854cf834e9f9
```

Extraction and scoring on the new rows queue behind the steering jobs.

**Third audit launched (overdue — should have run at tick 24).** Pointed at the claims currently
standing, not the ones already retracted. Two briefs I aimed at my own weakest points:

- **C2 may be measuring a bad refusal probe rather than refusal's unimportance.** The audit checks
  whether the house refusal direction separates `direct_harmful` from benign at all on this model;
  if it does not, "Boombness dominates refusalness" is a statement about the probe.
- **C3's headline comparison changes edge count (56832 vs 3552) at the same time as layer
  coverage**, so it may not isolate depth-distribution at all.

Also asked: are the coherence thresholds post-hoc fitted to make α=1 fail, and is the random
control at 0.466 unique-word ratio (baseline 0.741) itself partly degenerate and therefore not a
clean control?

### 2026-08-17 — Tick 26 (the steering dose–coherence curve; both low doses are clean)

All four steering doses through `coherence_gate.py`, against the un-intervened baseline:

| arm (add `d_surface` @ L8, gap units) | uniq-word | 3-gram repeat | top-word | truncated | verdict |
|---|---|---|---|---|---|
| baseline (no intervention) | 0.741 | 0.017 | 0.101 | 37% | OK |
| **α = 0.10** | 0.761 | 0.014 | 0.097 | 48% | **OK** |
| **α = 0.25** | 0.861 | 0.006 | 0.093 | 30% | **OK** |
| α = 1.00 | 0.302 | 0.551 | 0.139 | 100% | **DEGENERATE** |
| α = 2.00 | 0.051 | 0.848 | 0.651 | 100% | **DEGENERATE** |

**The model tolerates a quarter of a diff-of-means along this axis and collapses well before a
whole one.** Between α=0.25 and α=1 the trigram repetition rate goes from 0.006 to 0.551 — that is
not a gradual degradation, it is a cliff. Anything reported at α≥1 is a statement about a broken
model, which is exactly what the retracted 3.5×-ASR result was.

Worth noting for §12: a GCG-style objective that maximizes this projection has no reason to stop at
0.25. If the usable range is this narrow, "optimize Boombness" needs an explicit coherence
constraint in the objective, not just in the evaluation — otherwise the optimizer will find the
degenerate regime, and the judge will score it as success.

Both clean arms are now being judged; **their ASR is the actual G4 causal test**, and unlike the
α=1 run it will be readable.

---

## G4 steering, coherent dose — the effect runs OPPOSITE to the hypothesis (preliminary)

`steer_L8_a025`, coherence **PASSED** (uniq 0.861, 3-gram 0.006, 30% truncated — cleaner than
baseline), 660 generations, judge null_frac 0.0000.

| arm | ASR@0.5 | mean score | **refusal** |
|---|---|---|---|
| baseline (no intervention) | 0.219 | 0.188 | **0.074** |
| **`d_surface` @ L8, α=0.25** | **0.082** | 0.074 | **0.696** |
| — direct_harmful under the same intervention | 0.000 | 0.000 | 1.000 |

**Adding Boombness cut the attack's success by 63% (0.219 → 0.082) and raised refusal nearly
tenfold (7% → 70%).**

If Boombness were the mechanism the attack exploits, pushing the codeword *toward* the concept
should make the attack work **better**. It does the opposite, and strongly. The natural reading is
that doublespeak succeeds by **hiding** the harmful concept from the safety machinery, and making
the codeword more concept-like **un-hides it** — the model then recognises the request and refuses.

That is a coherent story, and it is consistent with G2 (Boombness correlates with ASR **within** the
arm) only if the correlation is not causal in the direction assumed — which is precisely why the
plan asks for a steering test rather than stopping at a correlation.

### I am NOT calling this yet — the control that decides it is running

The missing comparison is a **norm-matched perturbation at the same dose**. Without it I cannot
separate:

- **(i)** `d_surface` specifically un-hides the concept and triggers refusal, versus
- **(ii)** *any* perturbation of this magnitude at L8 disturbs the prompt enough to trigger refusal.

The α=1 random control is useless here — it was degenerate. Three arms now running at the coherent
dose:

| job | arm | question it answers |
|---|---|---|
| 760929 | `random` @ α=0.25 | is it the axis, or any perturbation? |
| 760930 | `orthogonal` @ α=0.25 | same, with an independent draw (the two were previously the *same* draw) |
| 760931 | `d_surface` @ **α = −0.25** | does pushing AWAY from the concept *raise* ASR? |

The negative-direction arm is the sharp test. If the mechanism is "concept-ness is hidden", steering
away from the concept should push ASR **above** baseline. If instead both signs reduce ASR, the
effect is disturbance, not direction, and this whole reading collapses.

---

## CORRECTION to G2 and §9 Q6/Q7 — both claims survive, both magnitudes were inflated by selection

Third audit: 26 candidates, **25 confirmed**. Two hit the standing claims. Neither reverses a
direction; both mean I quoted numbers that were larger than the evidence supports, and in both
cases the inflation came from **a selection that favoured my hypothesis**.

### C1 — the L8 headline was half residual-stream norm

`d_surface|L|proj` is an *unnormalised* inner product, so it scales with `‖h‖`. The norm is itself
an ASR predictor, and `analyze_g2.py` never controlled for it even though `extract_boombness`
writes `hnorm|L0..L31` into the very rows it reads. Now it does:

| predictor | ρ | ρ given ‖h‖ | ‖h‖ vs ASR | norm share |
|---|---|---|---|---|
| **`d_surface` L8 proj** (my headline) | +0.342 | **+0.172** | −0.315 | **50%** |
| **`d_surface` L12 proj** | +0.307 | **+0.302** | −0.059 | **2%** |
| `d_surface` L31 proj | +0.273 | +0.287 | +0.204 | −5% |

**Half of my headline was a nuisance scalar.** Worse, I selected L8 by argmax over 28 correlated
columns — and it is the single most norm-contaminated layer of the ten. The norm-free value at L8
(+0.172) would not clear Holm over that family.

**Corrected headline: `d_surface` L12 proj, ρ = +0.307, norm-partial ρ = +0.302 (p = 2.6e-06),
positive in 5 of 6 domains.** The claim "Boombness predicts ASR within the doublespeak arm"
**survives cleanly** — at a different layer, with a control I should have run.

The script now prints the partial and flags any predictor where >⅓ of the association is norm.

### C2 — the "40×" over refusalness was a selection artifact

I compared refusalness pinned at **L18 (near its own minimum, R²=0.0032)** against the
**argmax-selected** Boombness column, then quoted the ratio. Given the same freedom:

| | R² |
|---|---|
| refusalness, **best** single layer (L12) | **0.0386** |
| refusalness, all 5 layers jointly | **0.0725** |
| `d_surface` L12 proj | 0.1411 |
| Boombness adds over refusalness-L12 | **+0.1044** |
| **refusalness (all layers) adds over Boombness** | **+0.0393** |

**Honest ratio: 3.7× in-sample (3.0× cross-validated), not 40×. Refusalness adds +0.039 over
Boombness, not +0.0005.** The direction holds; the magnitude does not.

Two things the audit established that I should have stated originally:
- **The refusal probe is fine** — it separates the arms by ~9σ (`direct_harmful` +7.30 vs
  `natural_doublespeak` +0.04). The low within-arm R² is **range restriction** (within-arm sd 0.74
  vs pooled 3.07), so "refusal is unimportant" is only true *within the attack arm* and must never
  be quoted as a general statement.
- **The two predictors are read at different token positions** (refusalness at the last token,
  `d_surface` at `codeword_last`), so part of "Boombness beats refusalness" is "the codeword
  position beats the last position". That is a footing mismatch, not a fair contest.

### The pattern, again

Three retractions were *manipulated ≠ measured*. These two are its sibling: **compare-the-best-of-mine
against-a-fixed-instance-of-yours**. Same root — an asymmetry that happens to point the way I
expected — and it survived my own review both times because the number looked plausible.

### 2026-08-17 — Tick 27 (control arms lost to a zsh expansion bug, twice)

The two matched controls for the G4 steering result (`random`, `orthogonal` at α=0.25) both **FAILED
at launch**, and the cause was the shell, not the code:

```
wrote:  --intervene $d:add:8-8:0.25          with d=random
got:    --intervene /home/.../randomdd:8-8:0.25
```

**`$d:a` is zsh's absolute-path history modifier**, so `$d:add` expanded to `<abs path>` + `dd`.
The job then died inside Python on `ValueError: not enough values to unpack (expected 4, got 3)` —
an error two steps removed from its cause, pointing at the parser rather than at the shell.

The retry hit **the other** documented zsh hazard: `set -- $spec` does not word-split an unquoted
variable in zsh, so `$1` became the whole string and the configs came out worse. Both are in my
memory file already; I wrote the note after the `git commit -m` quoting failures and then walked
into the same family twice in one tick.

Fixed by building the files with `printf` and **grepping them back** before submitting — which is
now the rule, because a generated config that looks right in the script can be wrong on disk and
the failure surfaces where the shell is no longer visible. Memory updated
(`feedback_zsh_expansion_hazards`).

Jobs **760954** (`random`) and **760955** (`orthogonal`) relaunched with verified args; **760931**
(`d_surface` at α = −0.25, the sign-flip falsifier) running.

### 2026-08-17 — Tick 28 (the steering dose–response, still uninterpreted pending controls)

`steer_L8_a010` judged: 660 generations, null_frac 0.0000, coherence PASSED.

| α (gap units, `d_surface` @ L8) | coherence | ASR@0.5 | 95% CI | refusal |
|---|---|---|---|---|
| 0 (baseline) | OK | 0.219 | [0.173, 0.272] | 0.074 |
| **0.10** | OK | **0.241** | [0.194, 0.295] | 0.144 |
| **0.25** | OK | **0.082** | [0.054, 0.120] | 0.696 |
| 1.00 | **DEGENERATE** | (0.759) | — | 0.000 |
| 2.00 | **DEGENERATE** | (0.000) | — | 0.000 |

**α=0.10 is indistinguishable from baseline** — 0.241 vs 0.219 with overlapping intervals. The
suppression appears only at α=0.25, where ASR falls to 0.082 and refusal rises to 0.696.

So the usable dose window is narrow *and* the response inside it is not gradual: nothing at 0.10,
a large suppression at 0.25, incoherence by 1.0. Whether that is a threshold in the mechanism or
just the onset of disturbance is exactly what the three running controls decide, and I am not
reading the pattern until they land.

Running: **760954** `random` @ 0.25 · **760955** `orthogonal` @ 0.25 · **760931** `d_surface` @
**−0.25** (the sign-flip falsifier).

### 2026-08-17 — Tick 29 (population mismatch caught before comparing; `analyze_steering.py`)

The sign-flip arm finished with **960** behavioural prompts, while the baseline and the α=+0.25 arm
have **660** — the bank was expanded for §11 between those launches. Comparing their headline ASRs
directly would have compared **different prompt populations**, which is the same
*manipulated ≠ measured* class that produced all three retractions.

Caught before comparing, and handled in a committed script rather than by hand.
**`src/boombness/analyze_steering.py`**:

1. **intersects the arms on `prompt_id`** and reports each arm's coverage of the common set; every
   number is computed on that set only;
2. **refuses to report an arm that fails `coherence_gate`** — the retracted α=1 "3.5×" is exactly
   what that guard exists for;
3. reports **paired** Δscore against baseline, since all arms score the same prompts;
4. encodes the **sign test** explicitly, including the outcome that kills the story:

```
BOTH SIGNS SUPPRESS  -> the effect is DISTURBANCE, not direction.
                        No mechanistic reading of the axis is available.
SIGNS OPPOSE         -> the effect follows the axis direction.
```

Writing the falsifying branch into the script *before* seeing the numbers is deliberate: the
appealing interpretation is already available and I would rather the code state the condition under
which it fails than decide after the fact.

Sign-flip arm judging now; `random` and `orthogonal` at α=0.25 still generating.

### 2026-08-17 — Tick 30 (sign-flip arm clean; awaiting the last control)

`steer_neg_a025` (`d_surface` @ L8, **α = −0.25**) completed with 960 generations, 0 failures, and
**passes coherence** (uniq 0.710, 3-gram 0.020, 14% truncated — closest of any intervened arm to
the un-intervened baseline). So the falsifier is measurable rather than degenerate, which is the
condition it needed to be informative.

Judging in progress for the sign-flip arm and the `orthogonal` control; `random` still generating.
`analyze_steering.py` runs once all three land, on the intersected prompt set, with the sign test
decided by the script.

**What each outcome would mean, fixed now:**

| result | reading |
|---|---|
| +0.25 suppresses, −0.25 **raises** ASR | the effect follows the axis — concept-ness is causally related to attack success, in the direction that *more* concept-ness means *less* success |
| **both signs suppress** | **disturbance, not direction** — the α=+0.25 result is a shove, and the "doublespeak hides the concept" reading is dead |
| neither moves vs the controls | the axis is causally inert at coherent doses; §12's objective has no causal support |

The middle row is the one I consider most likely on the evidence so far, because the α=0.10 arm did
nothing and the jump to suppression at 0.25 has the shape of a tolerance threshold rather than a
graded mechanistic response.

### 2026-08-17 — Tick 31 (all five steering arms generated; controls are clean)

Coherence gate on every arm at the coherent dose:

| arm | uniq-word | 3-gram | truncated | verdict |
|---|---|---|---|---|
| baseline | 0.741 | 0.017 | 37% | OK |
| `d_surface` +0.25 | 0.861 | 0.006 | 30% | OK |
| **`d_surface` −0.25** | 0.710 | 0.020 | 14% | OK |
| **`random` +0.25** | 0.732 | 0.017 | 32% | OK |
| **`orthogonal` +0.25** | 0.739 | 0.015 | 29% | OK |

**All five are coherent**, and the two controls sit essentially on top of the baseline (0.732 /
0.739 vs 0.741). That matters: the α=1 random control was itself half-degenerate (0.466) and could
not have served as a comparison. At α=0.25 the norm-matched perturbations leave generation intact,
so any ASR difference between `d_surface` and them is attributable to the direction rather than to
damage.

That is the condition under which the sign test is meaningful, and it now holds. Judges running for
the sign-flip arm and both controls; `analyze_steering.py` produces the verdict on the intersected
prompt set as soon as they land.

### 2026-08-17 — Tick 33 (two of three steering judges done; NOT reading them yet)

`steer_neg_a025` and `ctrl_orth_a025` finished (960 generations each, 420 in the doublespeak arm).
Raw per-arm numbers exist, but **they are on a different prompt population than the baseline and the
α=+0.25 arm** (960-row bank vs 660-row bank), so reading them side by side is precisely the mistake
`analyze_steering.py` was written to prevent. Recording that I have seen them and am not
interpreting them until the intersected comparison runs.

`ctrl_rand_a025` at 928/960. The verdict comes from the script, on the common prompt set, with the
sign branches fixed in code before the numbers arrived.

---

## ✅ GATE G4 — NEGATIVE. Steering does not support a directional causal claim.

`analyze_steering.py`, **common prompt set = 270** (every arm intersected on `prompt_id`; the
post-expansion arms cover 64.3% of their own 420 and 100% of the common set). All intervened arms
passed the coherence gate. Paired Δ(StrongReject) against the same baseline prompts:

| arm | ASR | 95% CI | refusal | **paired Δscore** |
|---|---|---|---|---|
| baseline | 0.219 | [0.173, 0.272] | 0.074 | — |
| `d_surface` **+0.25** | 0.081 | [0.054, 0.120] | **0.696** | **−0.1144 ± 0.0235** |
| `d_surface` **−0.25** | 0.148 | [0.111, 0.195] | 0.067 | **−0.0741 ± 0.0198** |
| `random` +0.25 | 0.178 | [0.137, 0.228] | 0.085 | −0.0352 ± 0.0177 |
| `orthogonal` +0.25 | 0.189 | [0.147, 0.240] | 0.093 | −0.0306 ± 0.0179 |

**BOTH SIGNS SUPPRESS ASR.** The verdict the script prints is the one that was fixed in code before
the numbers existed:

> BOTH SIGNS SUPPRESS → the effect is DISTURBANCE, not direction. No mechanistic reading of the
> axis is available from this.

So the α=+0.25 result — ASR 0.219 → 0.081, a 63% reduction — **is not evidence that Boombness
causes the attack.** Pushing the codeword *away* from the concept suppresses the attack too.

### Two things that are nevertheless real, and worth keeping

1. **The axis is not inert.** `d_surface` perturbation suppresses ~2–3× more than a norm-matched
   perturbation at the same dose (Δ −0.114 / −0.074 vs −0.035 / −0.031, and the control Δs are
   themselves ~2σ). The attack is *more* sensitive to displacement along this axis than to
   displacement in general — it is just not sensitive to the **sign**.
2. **Refusal responds directionally even though ASR does not.** `+0.25` drives refusal to **0.696**
   while `−0.25` leaves it at **0.067** and the controls at 0.085/0.093 — a ~10× asymmetry that
   *does* track the sign. So the two signs suppress the attack by **different routes**: adding
   concept-ness triggers refusal, removing it does not. That asymmetry is a single arm each and is
   flagged as suggestive, not established.

### §18 outcome label

This is the plan's **outcome B — mechanistic but not causal**: Boombness is measurable, predicts ASR
within the attack arm (ρ=+0.307 at L12, norm-controlled), and its manipulation moves behaviour — but
**not in a way whose sign follows the axis**, which is what a causal reading requires and what a GCG
objective would need.

**Consequence for §12:** an objective maximizing `⟨h, d_surface⟩` has no directional causal support.
The correlation is real; the intervention says the model's attack-success is destabilized by
movement along this axis rather than driven by position on it. Building the optimizer on the
correlation alone would have produced a result that this experiment says is not there.

**This is the gate working exactly as the plan intended** — §12 is explicitly conditional on the
earlier gates, and this is the condition failing.


### Tick 35 — 2026-08-17

All four gates are answered and the queue is empty, so this tick did three things.

**Closed §12 as a documented negative.** P8.2/8.3/8.4 were gated on a directional causal result that
G4 did not deliver. They are marked CLOSED — gate not met rather than TODO: not running them is the
finding, and the plan made them conditional precisely so this decision would be forced by data.

**Unblocked P7.4.** `role_analysis.json` was still reading the pre-expansion extract — 12 extract
rows and 6 judged rows per role style, which is why §11 was marked BLOCKED. The expanded bank has
72 behavioural rows per style, so jobs 761148 (extract, 2352 rows) and 761149 (base generation, 960
behavioural) went out. Worth flagging what the underpowered table already hints: Boombness is
**flat** across role styles (L12 cos −0.293 to −0.304 across all six) while mean ASR ranges 0.00 to
0.20. If that survives the powered rerun it is §11's answer (b) — role framing moves behaviour
without moving the axis — which is consistent with G4's negative and, unlike G4, is a positive
claim. It is NOT quotable yet at n=6.

**Fourth audit launched** against the claims that will appear in the final report rather than the
ones already retracted. Two auditors: one trying to refute the G4 conclusion itself (is the −0.25
arm the true negation of the same direction; are the controls norm-matched **in gap units**, since
a dosing mismatch would make "2–3× the controls" an artifact of dose rather than of axis; is the
sign-test's arm-name string matching mislabelling `pos`/`neg`); one on retraction leakage plus
re-derivation of the four headline numbers, pointed at three specific fairness problems I suspect
in my own work — whether the 3.7× is an R² ratio between models of **different dimensionality**
(several Boombness layer columns vs one refusalness column), whether the G1 CI of +23% to +135% is
a ratio with a noisy denominator at n=8, and whether G3's 84%-vs-0.1% is confounded by **edge
count** (56832 vs 3552 vs 16) rather than by layer spread.

**The full report is deliberately not written yet.** Two of those checks can change sentences in it,
and writing the final document before the audit that could invalidate it is the exact ordering that
produced retractions R1–R3.


## Audit 4 (2026-08-17) — G4 conclusion + provenance

### A4-1 — CONFIRMED BUG: the coherence gate was silently non-binding. **Fixed, re-run.**
`analyze_steering.py` took the arm name from the **judge** dir's tag but the coherence key from the
**score_behavior** dirname — `steer_a025` vs `steer_L8_a025`, `baseline` vs `base`. Every lookup
missed, `coherent` came back `None`, and the gate tested `coherent is not False`, so **`None`
passed as if it had been checked**. The gate that exists specifically to stop another retracted
α=1 result was not protecting the two arms it most needed to.

Fix: resolve coherence through the **recorded linkage** (`judge/config.json → args.gens`), never a
filename; `coherent is None` is now **fatal** unless `--allow-missing-coherence` is passed
explicitly. Re-ran: **all five arms OK, every number identical.** No GPU rerun, no number changed —
but the progress doc's claim "all intervened arms passed the coherence gate" was, when written,
**not supported by the artifact it cited** (`steering_analysis.json` recorded `null`, not `true`).
That sentence is corrected above.

Sub-fix: `coherence_gate.assess` pooled **all conditions and all prompts** in a run rather than the
condition and common prompt set being reported, and silently drops texts under 8 words — which
excluded 68 of the +0.25 arm's 270 doublespeak generations, i.e. exactly the refusals the
intervention produces. `assess()` now takes `condition`/`keep_ids` and reports `n_dropped_short`.

### C3 — CORRECTION: "2–3× the controls" was never actually computed, and is sign-dependent.
The script only compared each arm to baseline; it never contrasted arm against control, so the
"2–3×" was eyeballed from two independent means. Now computed as **paired** contrasts on the same
270 prompts:

| contrast | Δ | z |
|---|---|---|
| +0.25 − orthogonal | −0.0838 ± 0.0230 | **−3.6** |
| +0.25 − random | −0.0792 ± 0.0221 | **−3.6** |
| −0.25 − orthogonal | −0.0435 ± 0.0192 | −2.3 |
| −0.25 − random | −0.0389 ± 0.0185 | −2.1 |
| +0.25 − (−0.25) | −0.0403 ± 0.0207 | −1.9 |

So **"the axis is not inert" is solid for +0.25 and weak for −0.25** (~2σ uncorrected, over two
comparisons). Stating one blended "2–3×" over both signs overstated the negative arm. Corrected.

### A4-2 — SUBSTANTIVE: the verdict flattened two different mechanisms. **Verdict reworded.**
The sign test reads only mean StrongReject and is blind to *how* each arm suppresses. Of the
prompts each arm suppressed, the fraction that are keyword refusals:

| arm | n suppressed | refusal fraction |
|---|---|---|
| **+0.25** | 71 | **0.901** |
| **−0.25** | 64 | **0.000** |
| random | 55 | 0.000 |
| orthogonal | 48 | 0.042 |

`+α` is a **refusal trigger**; `−α` is a **generic degradation statistically indistinguishable from
the norm-matched controls**. "Both signs suppress, therefore pure disturbance" is too strong — it is
true that ASR does not follow the sign, which is what kills the attack objective, but the two arms
are not doing the same thing. `analyze_steering.py` now computes the route table and the verdict
string refuses to say "disturbance" unqualified when the routes differ by >0.3.

### A4-3 — REFUTED: provenance. And the zsh hazard bit *me* mid-audit.
The auditor reported `src/boombness/` untracked with run-recorded shas missing the code. Both are
wrong: 26 files tracked, present in HEAD. My own verification *reproduced* the auditor's false
result until I noticed why — I wrote `git cat-file -e $s:src/boombness/...` and **zsh parsed `:s`
as the substitution history modifier**, mangling the path. Braced, it resolves, and the stronger
fact is available: `score_behavior.py` is blob `08775968` — **byte-identical at the +0.25 run's
sha, the −0.25 run's sha, and HEAD**. So the thing the auditor called unprovable (same intervention
code across arms) is positively proven. This is the third time `feedback_zsh_expansion_hazards` has
fired; it now has an audit-level example.

Still open: `metadata.json` and `RUNMETA.json` in the same run dir record **different**
`git_commit` values. Real defect, cosmetic here (both contain identical code), worth fixing.

### A4-4 — ACTED: controls rested on n=2 draws.
Each control was a **single** random vector; the ±0.018 SEMs are prompt-level only and carry no
direction-level variance, so "more than a random perturbation" leaned on two draws that happened to
agree. Four more random draws launched (seeds 20260817–20 → jobs 761172–5) to turn that into a
proper control band.

### A4-5 — NOT ACTED, disclosed: scope mismatch between fitting and intervening.
`d_surface` is fitted at the **codeword-occurrence token**, but the intervention adds it at **every
position and every decode step**. "The axis is not inert" is therefore a claim about a global
injection, not about the representation at the token the axis was fitted on. A position-scoped add
is the fair test; not run, and the limitation is now stated rather than papered over.

### Verified clean (attempted refutations that failed)
- The −0.25 arm **is** the exact negation of the same fitted direction: same `fit-dir`, same layer,
  same direction file, alpha the sole sign carrier, no `abs()`, no re-normalization. Layer
  convention confirmed (fit at `hs[L+1]`, hook on block 8 — no off-by-one). Greedy decoding, so no
  RNG confound from the 660- vs 960-row banks.
- Controls **are** dosed in gap units: they take `gap["d_surface"]`, so all four intervened arms
  inject magnitude 0.25 × 6.0549 = 1.5137. Identical dose. cos(rand, d)=−0.0005, cos(orth, d)=7e−9,
  cos(rand, orth)=0.019 — genuinely independent draws. **The recurring gap-unit bug did not recur.**
- Intersection genuinely covers baseline; 0 null scores, 0 duplicate ids, and `prompt_sha16`
  identical across arms for all shared rows.
- `refused` is one code path for all arms; every refused row has StrongReject exactly 0.0.


### Tick 35b — launch failure worth recording

All six jobs (761148/761149/761172–5) **FAILED in 3–7 seconds**. Cause: I wrote the argsfiles into
the session scratchpad under `/tmp`, which is **node-local** — the file exists on the login node and
not on `n-802`. The wrapper's guard printed `ERROR argsfile not found: ...` and exited 1, so nothing
ran with empty arguments; the failure was loud, which is the only reason it cost seconds rather than a
silent bad run.

Worth noting *how* it presented: the jobs vanished from `squeue` within seconds, which looks exactly
like "they finished". `sacct --starttime now-40minutes` showed `FAILED / 00:00:03`. Relaunched with
argsfiles under `outputs/boombness/argsfiles/` (shared filesystem) — all six started immediately.
Then four had landed on `n-803`, against the house cap of ~2 model-loading jobs per node, so two
were cancelled and resubmitted onto `n-805,t-806` via a **reduced `--nodelist`** (never `--exclude`
on the CLI, which would nullify the script's nodelist).

Recorded as a new memory (`feedback_slurm_argsfile_shared_fs`) since the scratchpad is the correct
default for every other temp file and this breaks only when a path crosses into a compute job.

## Audit 4, part 2 — standing claims. **RETRACTION #4 + three corrections + two dead guards.**

### ⛔ RETRACTION #4 — "the naive direction manufactures signal where the identified one finds none"
Short-update takeaway 2 was sourced entirely to the **Tick-7 section, which this sprint had already
retracted** (R1: "treat the Tick-7 section as superseded"). Its evidence was the L16–L20 "null
band", and R1 killed exactly that quantity. I then carried the conclusion into a collaborator-facing
report anyway. That is the worst failure mode in this log: not a wrong number, but a **retracted
number laundered into a summary**, where the retraction does not travel with it.

Re-derived from the committed `reanalyze_corrected.py` (`--metric d_naive|cos`, clustered p):

| L | 4 | 8 | 12 | 16 | 20 | 24 | 31 |
|---|---|---|---|---|---|---|---|
| `d_surface` | +0.023 | +0.027 | +0.015 | **−0.023** | **−0.029** | **−0.021** | +0.047 |
| p_clustered | 0.002 | 0.022 | 0.043 | **0.028** | **0.009** | 0.053 | 0.000 |
| `d_naive` | +0.043 | +0.048 | +0.037 | −0.006 | −0.016 | −0.005 | +0.094 |
| p_clustered | 0.000 | 0.003 | 0.001 | 0.437 | 0.074 | 0.623 | 0.000 |

"Roughly doubles" **survives** (1.75–2.4× at L4/L8/L12/L31). The rest is **reversed**: in the mid
band the *identified* direction finds a real negative displacement and the *naive* one is null, so
`d_naive` **attenuates a real effect** there — it does not manufacture a spurious one. Corrected in
revision 2 of the short update.

### C4 — the headline p-value ignored domain clustering (audit B1b)
`analyze_g2.py` had no clustering anywhere, re-introducing **the exact defect R1 named as its own
root cause** (pseudo-replication). The 234 prompts are 6 domains × 39 and ICC(predictor|domain)
≈ 0.45. Now computed by the committed script (`--cluster-by domain`):

| inference | p |
|---|---|
| i.i.d. (as reported) | 1.7e-06 |
| CR1 domain-clustered (G=6) | 1.2e-03 |
| **within-domain permutation — the one to cite** | **5.0e-04** |

The association survives — within-domain permutation destroys all between-domain signal and still
returns 5e-04, and domain fixed effects give ρ=+0.250 — so this is not a domain confound. But
**2.6e-06 was overstated by ~3.5 orders of magnitude** and is withdrawn.

### C5 — "positive in 5 of 6 domains" was the wrong column, and unsourced (audit B1c)
It is the `cos` column; the quoted predictor is `proj`, which is **6 of 6** — but two domains are
essentially null (`lab_safety` +0.020, `news_report` +0.062), so "5/6" and "6/6" both read as more
uniform than the data is. No committed script produced it, which is the same provenance failure as
R2. `analyze_g2.py` now emits the per-domain table.

### C6 — population mismatch between the headline table and the headline correlation (audit B2c)
The ASR table quoted `direct_codeword` **0.583** and doublespeak refusal **7.4%** over all 270 rows,
while the correlation uses the 234 with `n_examples ≥ 1`. On the same population those are **0.375**
and **0.9%** — the 12 zero-demo rows are all ASR=1.0 and carried the entire gap. Corrected.

Also corrected: the two mediation increments were quoted as a symmetric pair but were **1-vs-1
against 5-vs-1**; like for like, Boombness adds +0.104 and refusalness-joint adds +0.039. And the
**footing caveat C2 itself flagged as disqualifying was dropped on the way into the summary** —
refusalness is read at the last token, `d_surface` at `codeword_last`, so part of "Boombness beats
refusalness" is "the codeword position beats the last position". Restored.

### ☠ TWO GUARDS WERE SILENTLY INOPERATIVE
1. **The coherence gate never bound** (A4-1, fixed earlier this tick).
2. **The dynamic-range guard took `max` over SIGNED deltas** (`analyze_g1_g3.py`), so with every
   real arm negative it returned `random_nondemo` **+0.031** — a null control — as "the largest
   effect", and certified |3.53| > 3×|0.031| = True. Fixed to compare on magnitude. It now reports
   `dynamic_range_established=False`, and I restated what the guard is *for*: the question it
   protects is whether a **null** is interpretable, which needs only proof the readout is movable —
   established overwhelmingly by `no_demo_text` (−11.5) vs the largest null control (0.078). So
   `readout_movable=True`, `null_claims_interpretable=True`. The `False` must not be read as
   "G3 invalid".

Both guards were written *specifically* to prevent this sprint's earlier failures, and both passed
vacuously for days. **A guard that is never tested against a case it should fail is not a guard.**

### B4a — the depth-redundancy claim is NOT identified. **Downgraded; decisive arm running.**
`all_demo` (2 layers) and `all_layers_demo` (32 layers) cut the *same per-layer edge set*, so layer
spread and total edge count move together by exactly **16×** (3,552 vs 56,832). A pure edge-count
threshold explains every number equally well. And the data actively support that competitor: at
**fixed** 2 layers, 3,552 edges → Δ −0.008 but 7,200 edges → Δ **+3.53**, so "two layers cannot move
the readout" is **false**. Job 761188 runs the two arms that break the tie: `subsampled_all_layers_demo`
(3,552 edges over all 32 layers) and `dense_two_layer` (56,832 edges at 2 layers).

### B4b/B3a/B3b — over-precision and a fabricated interval
- "84% vs 0.1%" implies a 1000-fold separation; bootstrapped at n=6 it is **[62%, 110%]** vs
  **[−6.7%, +8.2%]** — the two-layer arm cannot exclude recovering 8%.
- **The G1 interval "+23% to +135%" was a chimera**: L8's lower bound welded to L18's upper bound.
  No arm has it.
- The delta-method CI was too **wide**, not too narrow — it propagated the span as if the endpoints
  were independent when they correlate **+0.63** within family, and used z=1.96 at n=8. A paired
  bootstrap over families now gives L18 **[+57%, +105%]** and L8 **[+54%, +88%]**, and reports that
  the 8 families come from only **2 domains**.

### B5 — provenance: no run records a bank content hash
Runs record a bank *path* and row count, but the bank at that path has been regenerated three times
(1464 → 1752 → 2352 rows). The phase board cited 1752-row evidence for runs that actually used 1464.
Nothing is currently wrong — the four headline runs agree at 1464 — but that is luck, and it is the
same "join across bank regenerations" hazard R1 named. `RunDir` should record `bank_content_sha16`.
Also: "0 alignment violations" is over the **216** families where the exact-swap invariant is
defined, not all 912; the numerator was quoted without its denominator. Corrected.

### Verified clean
Holm is correct textbook step-down and conservative over correlated columns (no inflation). R2 and
R3 do not leak. The 3.7× survives nested CV with selection inside the fold (3.65) and
leave-one-domain-out (+0.089 vs −0.067) — the most robust number in the sprint. The 59% semantic
dissociation reproduces exactly, and its clustered t (13.5) ≈ naive t (13.3).

## B4a RESOLVED — the depth framing was wrong; the redundancy is in the EDGE SET

Job 761188, same 6 families, all arms on one run:

| arm | edges | layers | edges/layer | Δ readout |
|---|---|---|---|---|
| `no_demo_text` (ceiling) | — | — | — | **−11.509** |
| `all_layers_demo` | 56,832 | 32 | 1,776 | **−9.708** |
| `dense_two_layer` | 7,264 | 2 | 3,632 | +0.496 |
| `positive_control` | 7,200 | 2 | 3,600 | +3.534 |
| `subsampled_all_layers_demo` | **3,552** | **32** | 111 | **+0.089** |
| `all_demo` | **3,552** | **2** | 1,776 | **−0.008** |

**The matched comparison is the last two rows, and it kills the depth reading.** At an identical
3,552 edges, spreading them over 32 layers instead of 2 changes the readout by **+0.10 log-odds** —
i.e. nothing, and in the wrong direction. **Layer spread is not the operative variable.** My
"distributed across depth, which is why every localized knockout reads zero" was wrong about the
mechanism.

**The other direction cannot be tested, and that is structural, not an oversight.** `dense_two_layer`
was meant to put 56,832 edges at 2 layers; it saturated at 7,264 because with `seq_len=114` and 32
heads a layer physically holds only ~3,648 edges. **Any cut above ~7.3k edges necessarily involves
more layers**, so edge count and layer spread cannot be decoupled upward. Identification here is
one-sided by construction — stated rather than hidden.

**What the data do support**, and it is a cleaner claim than the one it replaces: the demonstration
influence is carried by a **large, massively redundant edge set**. Removing **6.25%** of the demo
edges (3,552 of 56,832) does essentially nothing *regardless of how those edges are distributed over
depth*; removing 100% recovers 84% of the deletion ceiling. That is why every localized knockout —
top-k, bottom-k, random, same-head — reads zero: they are all removing ~0.03% of a redundant set.
The redundancy is in the **number of edges**, not specifically in their spread across layers.

Phase board and the short update are updated accordingly. This is the third claim this sprint whose
*mechanism* was wrong while its *observation* held, and the pattern is the same each time: a
comparison that moved two things at once.

### Tick 36 — 2026-08-17

Advanced the two audit follow-ups that do not depend on the running jobs.

**B5 provenance, fixed at the source.** `RunDir.note_bank()` now records the prompt bank's **content
hash** (`bank_content_sha16` + row count), not just its path, and it is wired into all six entry
points that consume a bank (extract, score_behavior, refusalness, surgical_knockout,
aggressive_patching, judge). The bank at the recorded path has been regenerated three times this
sprint (1464 → 1752 → 2352 rows), the phase board cited 1752-row evidence for runs that consumed
1464, and R1's stated root cause was joining across bank regenerations via a `prompt_id` that does
not hash prompt text. Nothing has gone wrong yet **only because the four headline runs happen to
agree at 1464** — which is luck, not a control. Current bank: `71bea179345ed118`, 2352 rows.

**The 3.7× fair-contest measurement is running (job 761192).** `refusalness.py` read the residual
stream at the **last prompt token** while `d_surface` is read at `codeword_last`, so part of
"Boombness beats refusalness 3.7×" was "the codeword position beats the last position" — the caveat
C2 itself called disqualifying, and which revision 1 of the update dropped. `--position
codeword_last` puts both predictors on the same token. Note this can only *weaken* my own headline:
if the gap collapses at matched position, the 3.7× goes, and that is the point of running it.

Still running: 761178 (base generation, 960 behavioural rows for §11), 761179/761180 (control
draws 1–2 of 4). Pending: 761184/761185 (control draws 3–4) and 761192. Watch the pending ones
against the 30-minute rule.

## ⛔ RETRACTION #5 — "Boombness beats refusalness 3.7× within the attack" was a POSITION ARTIFACT

The comparison read the two predictors at **different tokens**: `d_surface` at `codeword_last`,
refusalness at the **last prompt token**. C2 flagged this as "a footing mismatch, not a fair
contest" and I still shipped the 3.7× — twice. Job 761263 re-measured refusalness at
`codeword_last`, 960/960 rows, same 234 analysed prompts, same ASR, same script:

| | refusalness @ last token | refusalness @ **codeword_last** |
|---|---|---|
| best single-layer R² | 0.0386 | **0.1759** |
| all-layers joint R² | 0.0725 | **0.2565** |
| `d_surface|L12|proj` R² (unchanged) | 0.1411 | 0.1411 |
| **ratio Boombness / refusalness** | **3.66** | **0.80** |

**The ratio inverts.** At matched position refusalness is the *better* single predictor
(ρ = +0.405 at L18, p = 1.2e-10, vs Boombness +0.307), Boombness adds only **+0.038 to +0.076**
over it, and all five refusalness layers jointly add **+0.144** over Boombness. The entire 3.7×
was the codeword position beating the last position, not Boombness beating refusalness.

**This was called "the most robust number in the sprint"** — it survived nested CV with selection
inside the fold, and leave-one-domain-out. Both of those resample *rows*. **No amount of
resampling fixes a comparison whose two arms are measured at different places.** That is the
lesson: robustness checks test the estimate, not the contrast.

### What this does to the §18 label
§9 Q6 asked whether Boombness predicts ASR better than refusalness. The answer is now **no**. That
pushes the outcome from **B (mechanistic but not causal)** toward **C (refusal-suppression is the
story and Boombness is a correlate)** — which is also what G4 said from the intervention side:
`+d_surface` suppressed ASR by *triggering refusal* 90% of the time. The two independent lines now
agree, and they agree against my headline.

**Label pending one more cell.** The comparison is still only half-matched: I have `d_surface` at
`codeword_last` only. Job 761268 extracts it at the **last token** so the 2×2 (predictor × position)
is complete. If `d_surface@last` collapses the way refusalness@last did, then *position* is the
dominant factor for both and neither predictor is special; if it holds up, refusalness genuinely
wins at both positions. Either way the 3.7× is dead — I am running this to find out which
replacement claim is true, not to rescue it.

Short update revision 3 goes out once 761268 lands. Revision 2 is **withdrawn** on this point.

## The predictor × position 2×2 is complete. §18 label is now **C**.

Job 761268 supplied the missing cell (`d_surface` at the last prompt token). All four cells, same
234 prompts, same ASR, same script, single-predictor R²:

| | @ last token | @ codeword_last | position effect |
|---|---|---|---|
| `d_surface|L12|proj` | **0.0357** | 0.1411 | **4.0×** |
| refusalness (best layer) | 0.0386 | **0.1759** | **4.6×** |
| **ratio Boombness / refusalness** | **0.92** | **0.80** | |

Three things follow, and only the third is a claim I had before.

**1. Position dominates, for both probes.** Each is ~4–4.6× more predictive of ASR when read at the
codeword token than at the last prompt token. That is a larger factor than any difference *between*
the probes, and it was invisible while the two were measured at different places.

**2. At either matched position, refusalness is the better predictor** (ratio 0.92 at last, 0.80 at
codeword_last). **Q6's answer is NO.** The 3.7× existed only in the cross-position comparison.

**3. §18 outcome label: C — refusal-suppression is the story; Boombness is a correlate.**
Moved from B. Two independent lines now agree: the correlational side says refusalness ≥ Boombness
at matched position, and the interventional side (G4) says `+d_surface` suppresses ASR by
*triggering refusal* in 90.1% of the prompts it suppresses. Both point at refusal, not at concept
representation, and both point away from the objective the plan set out to build.

**What survives as a positive finding, and it is new:** the attack-relevant state is *localized at
the codeword token*. Whatever predicts jailbreak success in this attack is concentrated there rather
than at the final prompt position, for a concept probe and a refusal probe alike — which is
independently consistent with G1 (meaning retrieved into the codeword from the demonstrations at
answer time) and with G3 (that retrieval carried by a large redundant edge set). That is a
*position* result, not a *direction* result, and it is the one claim in this cluster that the
matched design supports rather than undermines.

**Caveat stated plainly:** the refusal direction was fitted for the last-token readout, so reading
it at the codeword token is off-label use. It is a legitimate *predictor* comparison — both probes
get identical treatment — but "refusalness at the codeword token" should not be read as a validated
refusal measurement at that position.

`outputs/boombness/position_2x2.json` holds the table.

### Tick 37 — 2026-08-17

`761268` closed the predictor×position 2×2 (above); §18 is now **C**. Short update taken to
**revision 3** — the first revision that changes the sprint's conclusion rather than tightening it,
so revisions 1 and 2 are explicitly withdrawn in its header.

**§11 (P7.4) is finally unblocked end-to-end.** `761178` produced 960 behavioural generations
including 72 per role style (vs 6 before), and the StrongReject judge is running over them now.
Note the judge **refused to start** on the first attempt because `OPENAI_API_KEY` was unset — it
declines rather than emitting all-null scores, on the grounds that a null must never be read as
benign. That guard behaved correctly, unlike the two that were found inoperative earlier today.

Control draws 3–4 (`761258`/`761259`) still running; with draws 1–2 that will give the 4-draw
control band the G4 "not inert" claim needs (audit A4-4).

### Tick 38 — 2026-08-17

**Three board rows closed, two of them by deciding NOT to run the experiment.** With §18 at C, some
planned work no longer produces information and saying so is better than quietly leaving it TODO:

- **P6.4 is DONE and it is what decided the label.** It needed no separate experiment — the
  matched-position analysis answers it directly. Both probes at `codeword_last`: refusalness alone
  R²=0.176 (0.257 jointly) vs Boombness 0.141; **adding Boombness to refusalness buys +0.012–0.076,
  adding refusalness to Boombness buys +0.144.** Boombness is close to redundant given refusalness.
- **P6.2 (head knockout) NOT RUN — superseded.** It asks which heads carry retrieval, but B4a showed
  removing 6.25% of demo edges does nothing *however distributed*. A per-head cut is 16 edges
  (~0.03%) and is therefore *guaranteed* to read zero, exactly as every localized arm already did.
  Running it would manufacture one more null with an obvious misreading attached.
- **P5.5 (Figure-9 plot) DROPPED.** It would plot the ASR-vs-Boombness relation that RETRACTION #5
  shows is not the operative one. A polished figure of a superseded framing is worse than no figure.
  If one is wanted, the honest figure is the predictor×position 2×2.

**Control band implemented** (audit A4-4): `analyze_steering.py` now aggregates `ctrl_rand_s<seed>`
arms into a band, reports the **between-draw** sd, and tests each steering arm against it by
combining prompt-level and between-draw error. Below 3 draws it refuses to express the comparison
rather than printing a supported-looking number. Regression-checked — every previously reported
figure reproduces unchanged. Four control judges are queued behind the §11 judge (869/960).

## §11 (P7.4) ANSWERED — powered. Role framing does not move the axis; its effect on ASR is **not established**.

`fullrole` extract (72 rows/style, was 12) + `baserole` judge (36 ASR rows/style, was 6), 6 styles
with demonstration content, domain, demo count and final query held FIXED:

| style | n_rep | Boombness L12 | n_asr | ASR |
|---|---|---|---|---|
| system_like_quoted | 72 | −0.2807 | 36 | **0.035** |
| assistant_like | 72 | −0.2876 | 36 | 0.160 |
| tool | 72 | −0.2858 | 36 | 0.163 |
| cot_like | 72 | −0.2820 | 36 | 0.177 |
| plain | 456 | −0.2909 | 204 | 0.195 |
| user_like | 72 | −0.2888 | 36 | **0.233** |

**Boombness is flat, and it is a TIGHT null, not an underpowered one.** `role → Boombness(L12)`:
**F = 0.175, p = 0.972**. The spread of the style means is **3.6%** of the within-style sd. Role
framing does not move the concept axis, and the design has the resolution to say so.

**⚠ I have to correct my own tick-35 speculation.** I wrote there that if the flatness survived the
powered rerun, §11's answer would be **(b) role → ASR directly, Boombness unmoved**. It did not
fully survive. `role → ASR`: **F = 1.94, p = 0.087** — the omnibus does not clear 0.05. The largest
pairwise gap (`system_like_quoted` 0.035 vs `user_like` 0.233, a 6.6× ratio) has Mann-Whitney
**p = 0.007 uncorrected**, which over 15 pairwise comparisons is **p ≈ 0.105 Bonferroni**. So the
ASR half is **suggestive and not established**.

**§11's answer is therefore (c)-leaning, not (b):** role framing definitively does not change
Boombness, and whether it changes ASR is unresolved at n=36/style. The mediation is consistent —
role adds only **+0.023** R² over Boombness, Boombness adds **+0.158** over role — but that
comparison inherits the position caveat from RETRACTION #5 and should not be read as "Boombness
beats role" in any strong sense.

**Why it matters anyway:** this is the cleanest dissociation in the sprint that runs the *other*
way. Every earlier dissociation was "the representation moves less than the behaviour". Here the
representation does not move *at all* across six framings, under a design that holds content
constant — which is exactly the constancy the Role-Confusion codebase's `render_single_message`
was ported for. Combined with outcome C, the picture is consistent: what varies with framing is not
the concept axis.

Caveat retained from the script: `role_style` is a **categorical proxy**; no Userness/CoTness probe
has been fitted on this model, so this is not a measured role signal.

### Retraction #5 — selection-fairness check (done before the audit reported, because it could have *over*-supported the retraction)

Refusalness's R² was a **best-of-5-layers** figure while `d_surface` was quoted at a fixed L12.
Selection inflates the winner, and here that asymmetry favours **refusalness** — i.e. it would make
my own retraction look better than it deserves. Checked, both probes @ `codeword_last`, n=234:

| refusalness layer | R² |
|---|---|
| L12 | 0.1342 |
| L14 | 0.1640 |
| L16 | **0.1313** (worst) |
| L18 (canonical) | 0.1647 |
| L20 | **0.1759** (best-of-5) |

| comparison | refusal | Boombness | ratio B/R |
|---|---|---|---|
| best-of-5 refusal vs best-of-3 Boombness | 0.1759 | 0.1411 | **0.80** |
| **fixed canonical L18** vs best-of-3 Boombness | 0.1647 | 0.1411 | **0.86** |
| refusalness' WORST layer vs best-of-3 Boombness | 0.1313 | 0.1411 | 1.07 |

**The retraction survives.** Against refusalness at **L18 — the canonical layer used everywhere else
in this repo and fixed long before this analysis** — Boombness still loses (0.86). Only by picking
refusalness's *worst* layer does Boombness edge ahead at 1.07, which is both cherry-picking and
inside the noise.

What matters most: **3.7× is not recoverable under any layer choice.** It would require refusalness
R² ≈ 0.038, and that value occurs only at the *wrong position*. The original ratio was a position
artifact, not a layer-selection artifact.

Noted separately: `d_surface` also enjoys a selection advantage the earlier audit flagged (~20
candidate columns vs refusalness's 5), and it is **refit** at each position (`stage=both`,
`fit_dir=None`, fresh `directions_fit_*.pt` written at `position=last`) while refusalness reads one
fixed direction at both positions. So `d_surface` got the better-fitted comparator at both cells
and still lost at both. The asymmetries run *against* Boombness, which makes the conclusion
conservative.

## ☠ THE §18 = C CONCLUSION WAS BUILT ON A PHANTOM CELL. Reverted to B-pending.

The audit launched to *attack* RETRACTION #5 found that the retraction is right but the
**replacement conclusion is not measured**. Verified independently before acting:

**`stage_score` never accepted `position`.** `--position` was threaded into `stage_fit`
(`extract_boombness.py:429`) but `stage_score` had no such parameter and read `hs[L+1, pos, :]` at
the codeword occurrence unconditionally. So `--position last` produced a run that **re-fit the
direction on last-token activations and then read it at the codeword** — a quantity nobody asked
for, reported under the label "d_surface at the last token".

Empirical confirmation I ran myself: `token_pos` is **identical to the codeword run in 1464/1464**
final-occurrence rows, and **0 of 2352** rows sit at `seq_len-1`.

### What that invalidates

| claim | status |
|---|---|
| the 3.7× was a footing mismatch and is withdrawn | **STANDS** — both numbers reproduce, read at different tokens |
| "at **either** matched position refusalness is better" | **WITHDRAWN** — only ONE matched position was measured |
| "position dominates for **both** probes (~4×)" | **WITHDRAWN** — true for refusalness (0.039→0.176, 4.6×, clean); **untested** for d_surface |
| §18 label = C | **REVERTED to B-pending** |

### And the one real cell is a tie, not an inversion
Domain-clustered bootstrap (6 domains, 4000 reps) on the single matched comparison:
`d_surface|L12|proj / refusalness|L20|proj` @codeword_last = **0.80, 95% CI [0.37, 1.24]**,
P(ratio>1) = 0.16; against the canonical L18, **0.86, CI [0.41, 1.23]**. **The CI covers 1.0 under
every resampling scheme**, so "refusalness is the better predictor" is not distinguishable from
"they are equivalent". My selection-fairness check last tick was correct as far as it went and still
missed this — it compared point estimates without an interval.

### A second, independent reason C was premature: construct validity
The auditor also checked whether `refusalness@codeword_last` still behaves like a refusal probe. By
condition, mean refusalness:

| condition | @last | @codeword_last |
|---|---|---|
| direct_harmful | **+7.298** | −1.971 |
| concept_in_benign_ctx | +6.290 | −1.955 |
| natural_doublespeak | +0.036 | −1.988 |
| benign_literal | −0.155 | **−2.429** |

At the last token the probe orders conditions exactly as a refusal probe should. **At the codeword
position that ordering collapses and partly inverts** — `direct_harmful` becomes indistinguishable
from doublespeak. It is not merely a restatement of `d_surface` (ρ = −0.03/−0.05 at L18/L20, and
the two combine near-additively, R² 0.141+0.176 → 0.250), but calling the winning quantity
"**refusal** suppression" is **not licensed by this run**. That bears directly on an A-vs-C label.

### Fixes applied
1. `position` threaded into `stage_score`; for `--position last` the per-occurrence loop collapses
   to the single final prompt token.
2. **A self-check on every row**: `--position last` asserts `pos == seq_len-1`, `--position
   codeword_last` asserts `pos` is a codeword occurrence. The phantom was invisible precisely
   because nothing ever asserted the readout index matched the request.
3. Job **761457** rerunning `--position last`.
4. Still owed, and recorded so it is not forgotten: give both probes the **same layer/stat freedom**
   in `analyze_g2.py` (it argmaxes refusalness over 5 layers against 3 hard-coded d_surface columns);
   at the last position that asymmetry alone is worth ~4×. And add a construct-validity assertion
   that whatever quantity wins at `codeword_last` still separates `direct_harmful` from
   `benign_literal`.

**The lesson, and it is the same one for the fourth time this sprint: I verified the *direction* of
the fix and not the *thing being measured*.** I checked that the last-position run refit its
directions (it did, freshly, at `position=last` — recorded in `summary.json`) and took that as
evidence the readout had moved. Fitting and reading are two different positions, and only one of
them changed.

## Audit 5, part 2 — the new analysis code. **A THIRD dead guard, plus two more.**

The second auditor went after everything written in the last few hours. Confirmed and fixed:

### ☠ B1 — the CONTROL BAND never fired. **Third dead guard this sprint.**
The band selected arms by `startswith("ctrl_rand_s")`, but arm names come from the **judge** dir
basename and the real runs are tagged `ctrlband_s<seed>`. **Zero arms ever matched.** The block took
its "<3 draws" branch every time and printed "only 0 draw(s)", while the `ctrlband_*` runs sat in
`ctrls` looking used. Fixed to accept both prefixes **and to print the arm names it did see** when
nothing matches, so an empty band can never again read as "the band was checked".

### ☠ C2/C3 — the movability guard used a blacklist and passed vacuously
`NULLABLE` was a *blacklist*, so every arm not named in it counted as a null control — including the
treatment arms added the same day. On the real edgematch run the threshold came from
**`dense_two_layer` (0.496)** instead of `topk_demo` (0.078): inflated **6.4×**, and made the
threshold depend on the effect under test. Worse, with an empty list the threshold collapsed to
`3 × 0.0`, so floating-point noise certified `readout_movable=True` — the same vacuous-pass shape as
the two guards already retracted. Now a **whitelist**, and an empty whitelist yields
`readout_movable=None` / `null_claims_interpretable=False`: movability with no null control is
**undefined, not passing**.

### ☠ F2 — `dense_two_layer` silently under-delivered by 87%
It requested 16× the demo edges at 2 layers and **silently truncated** when the pool ran out:
7,264 delivered of 56,832 needed. It now raises rather than quietly cutting 13% of target. My
tick-36 write-up did state the arm saturated and called the converse test impossible by
construction — **that reporting was correct** — but the code would have let a future run repeat it
silently. F1: the subsample fraction was hardcoded `//16`, correct only at exactly 2 chosen layers;
under the script's own default (4 layers) it silently produced **half** the intended edges while
still being labelled edge-count-matched. Now computed from `num_layers / len(chosen_layers)`.

### D3 — `readout_position` was recorded on every row and **read by nothing**
This is the RETRACTION #5 bug class left live: `analyze_g2.py` joined refusalness to the
representation on `prompt_id` with **no check that the two probes were measured at the same token**,
so the footing mismatch could be regenerated silently forever. `analyze_g2.py` now **refuses** when
the declared positions differ, and warns loudly when a pre-2026-08-17 run carries no position field.
**I tested it against a case it should fail** — a fixture with the position relabelled — and it
refused with the right message; on the legacy run it warned. Testing a guard against a failing case
is exactly the discipline the three dead guards lacked.

### A3 — the "CITE THIS ONE" permutation p was not a within-domain statistic
It permuted within domain but computed the slope from an **intercept-only** design. Within-group
shuffling preserves each group's mean of Y, so the between-domain component survived every draw and
the null was not centred on zero (null mean +0.100 vs observed +0.307 — a third of the statistic was
a fixed between-domain offset). Size stayed nominal, so nothing was falsely rejected, but power
depends on the **sign** of the between-domain slope (0.000 in the adverse case). Now group-demeans X
and Y first. **Re-ran: p is unchanged at 5.0e-04** (the 1/2001 resolution floor — 0 of 2000
permutations reached the observed value), so the headline survives with the correct statistic.

### B3 — the band's standard error was the SE of the band *mean*
`sd/√k` answers "where is the average random direction", but the question is whether an arm differs
from **one typical** random direction, which needs `sd·√(1+1/k)`. That understated direction-level
noise by √k and made "clears the band" too easy; the cutoff was also a normal z=2 where k=3 draws
need t(df=2)=4.30. Both fixed.

### Clean on inspection
`common.py note_bank()` (hashes content, records an explicit error on failure); the CR1 sandwich;
the within-domain permutation *indexing*; `_paired_boot_frac` (resamples families, preserves the
triple); `refusalness.py` `pos` definedness; `rng.permutation` usage across knockout arms.

**Running:** 761457 (`--position last` rerun with the readout actually moved, plus the new per-row
position assertion) and control-band judging (2 of 4 arms judged).

## The predictor × position 2×2, REBUILT on real cells. §18 settles at **B**.

Job 761457 reran `--position last` with the readout actually moved: **2352/2352 rows at
`seq_len-1`**, and the new per-row assertion would have raised otherwise. Rebuilt the table — and
caught a second freedom confound before quoting it: `d_surface` had **64** candidate columns at
`codeword_last` but only **20** at `last`, so the *position* comparison was not freedom-matched
either. Restricted to columns present at BOTH positions (20 for `d_surface`, 10 for refusalness),
same 234 prompts, same ASR, single-predictor R²:

| probe | @ last token | @ codeword_last | **position effect** |
|---|---|---|---|
| `d_surface` (20 common cols) | 0.0701 | 0.1411 | **2.0×** |
| refusalness (10 common cols) | 0.0455 | 0.1888 | **4.2×** |
| **ratio Boombness / refusalness** | **1.54** | **0.75** | |

Domain-clustered bootstrap (6 domains, 4000 reps):
- @last: ratio **1.54, 95% CI [0.64, 3.60]**, P(>1) = 0.89
- @codeword_last: ratio **0.75, 95% CI [0.33, 1.13]**, P(>1) = 0.10

### Three conclusions, and the middle one corrects yesterday's correction

**1. "Position dominates for both probes" is now MEASURED and it HOLDS** — 2.0× for `d_surface`,
4.2× for refusalness. It was withdrawn earlier today as resting on a phantom cell; with the real
cell it survives. **This is the sprint's surviving positive finding:** the ASR-predictive state is
localized at the **codeword token**, for a concept probe and a refusal probe alike, consistent with
G1 (meaning retrieved into the codeword) and G3 (retrieval carried by a large redundant edge set).

**2. "Refusalness is the better predictor" is FALSE as a general claim.** Which probe wins **depends
on where you read**: Boombness wins at the last token (1.54), refusalness at the codeword (0.75).
**Both CIs straddle 1.0**, so neither difference is significant at either position. The two probes
are comparable; position is the variable that matters.

**3. The 3.7× retraction STANDS, and is now fully explained.** The original compared
`d_surface`@codeword_last (0.141) against refusalness@last (0.039) — **the single most favourable
of the four possible cross-position pairings**, 3.66. No matched pairing reproduces anything like it.

### §18 FINAL LABEL: **B — mechanistic but not causal**
Not **C**: refusalness does not dominate; it only wins in one cell, insignificantly, and its
construct validity at that cell is doubtful (at the codeword position the probe no longer orders
`direct_harmful` above `benign_literal`, so calling that quantity "refusal" is not licensed).
Not **A**: Boombness does not beat refusalness at matched footing either, and G4 showed no
directional causal effect. **B** is where the evidence sits: Boombness is measurable, correlates
with ASR, localizes to the codeword — and does not support a steering objective.

`outputs/boombness/position_2x2.json` now holds the freedom-matched table and replaces the
phantom-cell version.

### Tick 40 — a self-inflicted skip, caught by not trusting "complete"

The control-band driver printed **"control band judging complete"** having judged **2 of 4** arms.
Cause: my own cleanup. Last tick I wrote an `ABORTED.json` marker into the two empty run dirs left by
the cancelled jobs — which **updated their mtime**, so the driver's `ls -1dt … | head -1` selected
the *empty* dir over the real 960-generation one and logged `SKIP (no gens)`.

Two things worth keeping from this:
1. **Selecting a run by mtime is fragile**, because any bookkeeping touch reorders it. The rerun
   selects by **content** — has a non-empty `gens.jsonl`, has no `ABORTED.json` — which is what the
   choice actually depends on. Same class as the coherence-gate bug: matching on an incidental
   property (a filename, a timestamp) rather than the recorded fact.
2. **A driver that reports "complete" while skipping most of its work is a reporting bug**, not just
   an operational one. It printed `SKIP` per arm, but the final line said complete, and a summary
   line that does not know what it skipped will be believed. If it had been trusted, the band would
   have been built from 2 draws and quietly failed the ≥3 threshold — reading as "not enough draws"
   rather than "the driver lost half your data".

Seeds 20260819/20260820 are judging now. The band is still **not** reportable until all four land.

### Tick 41 — the band block runs for the first time, and testing it caught an over-correction

The control-band block had **never executed** (audit B1: its selector never matched an arm name), so
before trusting it on the final data I ran it on the 3 draws already judged. Two things came out.

**1. My fix to the band's statistics over-corrected.** The original used `sd/√k` with a z=2 cutoff,
which the audit correctly called too permissive. I replaced it with the predictive spread
`sd·√(1+1/k)` and `t(df=k−1)` — and `df=k−1` is *as wrong in the conservative direction*. The
combined variance here is dominated by the arm's prompt-level term (0.0235 vs a band term of
0.0058), and **that** term carries ~269 df, not 2. Pooling at df=2 demands t > 4.30 for a quantity
whose uncertainty is almost entirely well-estimated. Now Welch–Satterthwaite, which weights each
component's df by its share of the variance: **df ≈ 168 here, not 2.** The verdict flips on this:

| arm | vs band | t | df | p | verdict |
|---|---|---|---|---|---|
| **+0.25** | −0.0770 ± 0.0244 | −3.2 | 168 | **0.0019** | **clears the band** |
| −0.25 | −0.0367 ± 0.0209 | −1.8 | 124 | 0.082 | does NOT clear |

**2. The band itself is remarkably tight.** Three independent random directions at the same dose
give −0.0343, −0.0338, −0.0440 — a between-draw sd of **0.0058**. Generic perturbation at this dose
produces a very reproducible ~−0.037 suppression, which is what makes the +0.25 arm's additional
−0.077 a real excess rather than draw-to-draw luck.

**This confirms C3 from a proper band rather than a single draw:** "the axis is not inert" is
established for **+0.25** and **not established** for **−0.25**. Same split as the paired contrasts
gave, now with direction-level variance actually estimated.

Fourth draw still judging (544/960); the band will be re-run on all four before anything is quoted.

**Worth stating plainly:** I got this statistic wrong twice in opposite directions, and only caught
it by running the block against real numbers instead of reading it. The dead guards in this sprint
share that cause — none of them was ever executed against a case whose answer was known.

## A4-4 RESOLVED — the random-control band, 4 independent draws. G4's "not inert" claim splits by sign.

All four draws judged (960 rows each), common 270-prompt set, every arm coherence-gated:

| draw | paired Δ |
|---|---|
| s20260819 | −0.0440 |
| s20260817 | −0.0343 |
| s20260820 | −0.0343 |
| s20260818 | −0.0338 |
| **band mean** | **−0.0366**, between-draw sd **0.0049** |

| arm | diff vs band | t | df (Welch) | p | verdict |
|---|---|---|---|---|---|
| **`d_surface` +0.25** | **−0.0778 ± 0.0241** | −3.23 | 235 | **0.0014** | **clears the band** |
| `d_surface` −0.25 | −0.0375 ± 0.0206 | −1.82 | 203 | 0.070 | **does NOT clear** |

**The claim "d_surface is not inert" is established for +0.25 and NOT established for −0.25.**
That is the same split the paired contrasts showed, now with direction-level variance genuinely
estimated instead of assumed from one draw — which is what audit A4-4 asked for.

Two things the band makes visible that a single draw could not:

**1. Generic perturbation at this dose is extremely reproducible.** Four independent random
directions land within 0.010 of each other (sd 0.0049), and the band contributes only ~5% of the
comparison's variance (`var_band` 0.000031 vs `var_arm` 0.000551). So the earlier worry — that
"more than a random direction" rested on a lucky draw — resolves in favour of the claim: random
directions at α=0.25 reliably suppress by ≈ −0.037, and +0.25 suppresses by more than twice that.

**2. It does not rescue the negative arm.** −0.25 sits at −0.0375 against a band mean of −0.0366 —
essentially **on** the band. The "axis-magnitude effect at both signs" reading from the original G4
write-up is therefore **half wrong**: only the positive sign exceeds a norm-matched random
perturbation.

### Net effect on the G4 statement
- **Both signs suppress ASR** → no directional causal claim, no attack objective. *(unchanged)*
- **+0.25 suppresses more than a random direction** (p=0.0014 vs a 4-draw band) and does so by
  **triggering refusal** (90.1% of its suppressed prompts). *(strengthened)*
- **−0.25 is indistinguishable from a random perturbation** (p=0.070) and suppresses via generic
  degradation (0% refusals, matching the controls). *(this is the correction)*

So the honest one-line G4 summary: **adding concept-ness to the codeword triggers refusal; removing
it just damages the model like any other perturbation of that size.**

### Tick 42 — I clobbered four board rows with an off-by-one, and had to recover them from git

Auditing my own bookkeeping this tick found that the tick-38 board update **silently destroyed two
rows and duplicated two others**. I edited by *line index* (`L[41]`, `L[42]`, `L[43]`), the indices
were off by one against the rows I meant, and the result was:

- **P6.1** (attention edge knockout, DONE) — **overwritten and lost**
- **P6.3** (direction knockout, DONE) — **overwritten and lost**
- **P5.5** and **P6.4** — my new rows *inserted*, the stale `TODO` originals left in place, so the
  board carried contradictory duplicate entries for two phases

Both lost rows are recovered from `00f1ba50^` and reinserted in order; both stale duplicates are
removed. Verified: **40 phase rows, no duplicates, ascending, and no id that has ever existed in the
file's history is absent now.**

**This is the same root cause as three of this sprint's bugs, in my own notes instead of the code:
addressing a thing by an incidental property (line number) rather than by its identity (row id).**
The coherence gate matched on a filename, the control band on a tag prefix, the run selector on an
mtime — and this on a line index. All four broke the moment something shifted. The repair and every
subsequent board edit now match on the row id.

Also closed four stale rows that later work had already answered: **P7.2** (superseded by P7.4's
powered tight null, F=0.175 p=0.972), **P7.3** (probes never fitted — `role_style` is disclosed as a
categorical proxy everywhere, not claimed as a measured role signal), **P8.1** (CLOSED, gate not
met — the steering prerequisite returned a directional null), **P8.5** (DONE at revision 4).

**Genuinely open, and honestly so:** P3.3 and P3.5 (probe + metric comparison, both REDO against the
headline extract) and P4.4 (§8 example-count sweep written up only as the layer surface in
`reanalyze_corrected.py`, no dedicated plots). These are the remaining real gaps and none of them
bears on a gate verdict.

## §6.3 probes (P3.3/P3.4/P3.5) — the existing suite was UNINFORMATIVE BY DESIGN. New surface-matched regimes added.

The four probe regimes had all been run against the headline extract, so these rows needed a
**write-up, not a rerun** — and writing them up is what exposed the problem.

### ⚠ d1–d4 return AUROC = **1.000 at every layer, in every regime**. That is not a result.
Every regime shared one label: `cell ∈ {B, E}` = "the target token IS the concept" — which is just
**the surface word**. `bomb` and `carrot` are trivially separable, so 1.000 everywhere is expected
and says nothing about whether the model builds a bombness representation. `d3_hard_negative` is
affected too: its C-vs-E test set is *also* a carrot-vs-bomb contrast. Shuffled-label controls sit
near chance (0.23–0.78), so the probes are not broken — the **task** was trivial.

**These 1.000s must never be quoted as "Boombness is linearly decodable."** That is exactly the
sentence they invite and it is not what they show.

### New regimes that hold the surface word CONSTANT and vary the meaning
- `d5_surface_matched_codeword` — A vs C, both surface **carrot**: does doublespeak context change
  the representation *at the codeword token*?
- `d6_surface_matched_concept` — B vs E, both surface **bomb**.

| layer | d5 AUROC | shuffled | d6 AUROC | shuffled |
|---|---|---|---|---|
| 0 | 0.960 | 0.561 | 0.974 | 0.376 |
| 8 | 0.984 | 0.468 | 0.985 | 0.629 |
| 12 | 0.982 | 0.571 | 0.985 | 0.408 |
| 31 | 0.983 | 0.657 | 0.979 | 0.594 |

### A confound I suspected and had to abandon
A/E prompts average **137.9** tokens and B/C **129.6**, with the codeword 8.3 tokens later — and that
difference tracks **context**, which is exactly the d5/d6 label. A probe reading length or position
would score well for the wrong reason. Tested directly: **`seq_len` alone gives AUROC 0.472 and
`token_pos` alone 0.473** — chance. The per-family direction is not even consistent (A's codeword is
later in only 42/72 families). **The confound is refuted; the d5/d6 result is real.**

### What d5/d6 do and do not establish
**Do:** with the surface word held constant, the codeword token's representation carries strong
information about which context preceded it — from block 0 onward, shuffled controls at chance, not
explained by length or position. This is a probe-side confirmation of G1's retrieval story: context
information reaches the codeword token.

**Do not:** establish that the retrieved content is specifically *bombness*. A and C differ in their
demonstration text, so a probe separating them shows the context is encoded there, not what it
encodes. The question "is the retrieved content the concept" is a projection question, and it is the
one the 2×2 (`d_surface` vs `d_context`) was built to answer — which is why the sprint's conclusions
rest on the projections rather than on these probes.

P3.3/P3.4/P3.5 are closed on that basis: the original regimes are uninformative by construction, the
new ones are informative but bounded, and neither changes a gate verdict.

## §8 (P4.4) — the demonstration-count dose-response. Three layer bands, and only one of them is dose-dependent.

The quantity is the **C − A** contrast on `d_surface|L|cos`: how much further along the Boombness
axis the token sits in **doublespeak** (C) than in **literal** use (A), with the surface word held
constant at `carrot` and demonstration count varied. Cluster-robust t over 6 domains, n=36 per cell.

| L | k=1 | k=2 | k=4 | k=8 | k=16 | monotone? |
|---|---|---|---|---|---|---|
| 0 | +0.0016 | +0.0000 | −0.0014 | −0.0022 | −0.0027 | — (≈0 throughout) |
| **4** | +0.0092 | +0.0141 | +0.0225 | +0.0307 | **+0.0384** | **4/4 increasing** |
| **8** | +0.0138 | +0.0169 | +0.0244 | +0.0359 | **+0.0449** | **4/4 increasing** |
| **12** | +0.0087 | +0.0114 | +0.0124 | +0.0178 | **+0.0269** | **4/4 increasing** |
| 16 | −0.0011 | −0.0082 | −0.0316 | **−0.0421** | −0.0319 | 4/4 *decreasing* to k=8 |
| 18 | +0.0006 | −0.0103 | −0.0347 | **−0.0483** | −0.0396 | 4/4 *decreasing* to k=8 |
| 20 | −0.0019 | −0.0152 | −0.0366 | **−0.0507** | −0.0420 | 4/4 *decreasing* to k=8 |
| 24 | +0.0054 | −0.0062 | −0.0240 | **−0.0419** | −0.0361 | 4/4 *decreasing* to k=8 |
| 28 | +0.0172 | +0.0095 | +0.0002 | −0.0159 | −0.0118 | sign flip in dose |
| **31** | +0.0485 | +0.0457 | +0.0485 | +0.0438 | +0.0499 | **FLAT — dose-independent** |

### Three bands, three behaviours
1. **L4–L12: positive and strictly dose-dependent.** Every step increases, 4/4, at all three layers.
   L8 grows **+0.0138 → +0.0449 (3.3×)** from one demonstration to sixteen. More demonstrations
   ⇒ the codeword sits further along the Boombness axis. This is the band where a "the model
   accumulates the mapping from examples" story is actually supported.
2. **L16–L24: negative, and the *magnitude* is dose-dependent, saturating at k=8.** L20 goes
   −0.002 → **−0.051** at k=8 and then back to −0.042 at k=16. So the mid-band displacement is not
   noise — it grows with evidence and then saturates — and it runs **opposite in sign** to the
   early band.
3. **L31: flat.** +0.0485 / +0.0457 / +0.0485 / +0.0438 / +0.0499 across a 16× change in
   demonstration count, at t = +5.9 to +10.2. **One demonstration achieves the entire output-layer
   effect**; fifteen more add nothing.

### Why this matters for the sprint's conclusions
- It gives the earlier "two humps" observation a proper account: **two bands of opposite sign that
  respond to demonstration count differently.** The retracted tick-7 claim called the mid band null;
  it is not null, it is negative *and dose-dependent*, which is a stronger statement than either the
  original claim or its retraction.
- **The output-layer effect saturates at k=1 while the mid-layer effects scale to k=8–16.** So the
  quantity that reaches the output is not a simple readout of the quantity that accumulates in the
  middle. That is consistent with G4's directional null: pushing on the axis mid-stack is not the
  same as moving what the output layer uses.
- Scale caveat, stated: these are cosines in the 0.01–0.05 range. The **sign structure and the dose
  response** are the findings; the magnitudes are small and should not be quoted as "the
  representation moves a lot".

### Tick 45 — all 40 board rows resolved; final verification launched

Every phase row is now DONE / CLOSED / DROPPED / NOT RUN / RETRACTED with a stated reason; nothing
remains quietly marked TODO. The queue is empty and the analysis is complete.

Rather than add more analysis, this tick launches a **final independent verification of the claims
still standing in revision 4** — the document that actually goes to collaborators. After five
retractions, three of which were caught by audit rather than by me, certifying the deliverable is
worth more than another experiment. The verifier is asked to re-derive all ten claim clusters from
committed artifacts and, specifically, to confirm the `lastpos` run really read at the last token
(the prior one did not) and that the corrected group-demeaned permutation p is the one reported.

The §15 full report is being written in parallel and will not be sent until that verification lands.


## ⚠ CORRECTION C7 — the L16–L24 negative band is a QUERY-KIND effect and fails Holm

The final verifier found that the mid-layer negative band, which §4 and §8 both lean on, is **absent
in the behavioural prompts** — the only population the ASR claims live on. From
`reanalyze_d_surface_cos.json`'s own `by_query_kind` block (cluster-robust t):

| L | behavioral | comprehension_usage | semantic_one_word |
|---|---|---|---|
| 16 | **+0.0027 (t=+0.3)** | −0.0344 (t=−4.1) | −0.0372 (t=−3.4) |
| 18 | **+0.0004 (t=+0.0)** | −0.0364 (t=−4.4) | −0.0434 (t=−3.7) |
| 20 | **−0.0041 (t=−0.6)** | −0.0374 (t=−4.6) | −0.0464 (t=−4.2) |
| 24 | **+0.0151 (t=+1.5)** | −0.0314 (t=−3.5) | −0.0454 (t=−3.6) |
| 31 | **+0.1327 (t=+9.8)** | +0.0001 (t=+0.0) | +0.0090 (t=+1.9) |

And the artifact's **own `holm_rejected` field is True only at L4 and L31** — L16–L24 are all False.
So quoting raw clustered p (0.009–0.053) as "a real negative displacement" was over-claiming against
a multiplicity correction the same file computes.

**What this changes:**
- §4's confound statement narrows to "the naive direction inflates ~2× where both agree". The
  "attenuates a real negative effect at L16–L24" half is a **semantic/comprehension** phenomenon.
- §8's dose-response keeps its structure but must be **labelled by query kind**: the L16–L24
  dose-dependent negative band is not a behavioural-prompt effect.
- It sharpens the last open caveat rather than adding a new one: G1/G3 run on `semantic_one_word`
  while G2/G4 run on `behavioral`, and the query-kind split does not merely risk a bad join — **it
  changes the sign of a reported effect.** For behavioural prompts the picture is simpler: early
  positive band (L8 +0.048 t=+2.1, L12 +0.036 t=+2.2), no mid-layer band, and a large L31 effect
  (+0.133, t=+9.8).
- Also corrected: the naive-direction p range is **0.074–0.62**, not 0.22–0.62; L20 was dropped from
  the range I quoted, and there the naive direction is also marginally negative.

## Audit 6 (final verification) — all 10 claim clusters certified numerically; **15 gaps found and fixed**

The verifier re-derived every standing claim from committed artifacts. **All ten clusters reproduce**,
including the three checks most likely to have been faked: the `lastpos` readout (2352/2352 at
`seq_len-1`), the knockout destination (72/72, `dst_mode: both`), and the cross-bank-regeneration join
(0/960 `prompt_sha16` mismatches, all 234 ids present in all five sources — the B5 hazard was real
but did not bite). It then found fifteen problems in revision 4, which was about to be sent.

### The two that were outright wrong
| # | problem | fix |
|---|---|---|
| 1 | The **"like for like" increment bullet** (+0.104 / +0.039) was itself built on the mixed footing the report retracts 30 lines earlier — refusalness@last vs `d_surface`@codeword. | Withdrawn. At matched footing **refusalness adds more at both positions**: +0.144 vs +0.028 @codeword, +0.091 vs +0.025 @last. Revision 4's bullet pointed the wrong way. |
| 2 | The **condition table** mixed populations *inside the paragraph claiming it no longer did*. Four of nine cells wrong, and **doublespeak refusalness flipped sign** (+0.04 → **−0.15**). | Recomputed on `n_examples ≥ 1`: harmful +7.06 / ASR 0.050 / 95.0%; doublespeak −0.15 / 0.214 / 0.85%; benign −0.30. The story survives and is cleaner. |

### Correction C7, the most scientifically significant (recorded separately above)
The L16–L24 negative band is **absent in behavioural prompts** and **fails the artifact's own Holm
field**. §4 and §8 both narrowed.

### The rest, all applied to both documents
3. **Three** dead guards, not two — the third is the control band behind this report's own "clears the band" claim. Also added: the movability blacklist (threshold inflated 6.4× by a treatment arm) and `dense_two_layer`'s silent 87% shortfall.
4. **Between-probe selection freedom is not matched** (20 vs 10 candidate columns), biasing the ratios toward Boombness. Disclosed, with the re-selecting bootstrap ([0.82, 2.88] and [0.40, 1.12]).
5. **G1's +84% is one arm of ~130**, and the all-layer variant of the same transplant moves the readout the *wrong* way (−0.76, CI [−1.49, −0.21]). Now named as the single-layer L18 window.
6. **The construct-validity sentence was wrong.** The probe *does* still order `direct_harmful` above `benign_literal` at the codeword position. What actually breaks: the gap **collapses ~16×** (7.45 → 0.46), `direct_harmful` becomes indistinguishable from doublespeak, and `direct_codeword` overtakes it. Still enough to withhold the name "refusal"; the reason is the collapse, not a reversal.
7. **The +0.25 arm's coherence verdict was computed on 202/270 rows** — 68 short generations skipped, on the one arm carrying a positive result.
8. **The "positive control" changes sign between runs** (+3.534 vs −1.135) and recovers ≈ −31% of the deletion span. Flagged; not to be cited as validating anything.
9. **G3 mixed units and signs** — raw log-odds vs percent-of-ceiling have opposite signs, so the subsampled arm's +0.089 is **−0.77%** of span. Matched-arm CIs added (±8% of ceiling).
10. p = 5.0e-04 is the **1/2001 resolution floor** → now `< 5e-4`.
11. "Shuffled controls at chance" → per-layer **0.354–0.716**; means ≈0.52 with ±0.2 scatter.
12. Role null now shown at **all three** tested layers (p 0.60 / 0.97 / 0.75), not the most favourable; "spread" relabelled as the **sd** of style means (range is 9.3%); ASR half described as **suggestive, not established**, on an unbalanced omnibus.
13. **Bank arithmetic** now states all three denominators: 912 families, 240 matched, 216 checkable.
14. **Gate table** rows for G1 and G4 still carried the retracted chimera CI and the retracted "2–3× the controls" wording. Both rewritten.
15. Stale "suggested next" items that were already done have been removed; the range-restriction sd corrected to **0.445** on the correlation population.

### Two provenance fixes the verifier forced
- **`analyze_position.py` is new and committed** — the headline position finding had no producer, and its CIs existed only in prose. The script matches freedom within probe, discloses the between-probe asymmetry, reports both bootstrap variants, and **verifies that every run read where it claims to.** It **refused on first use**: the legacy `@last` refusalness run carries no `readout_position`, so that cell's footing rested on reading the code. Job 761697 reruns it.
- **`g2_analysis.json` is quarantined** as `g2_analysis_MIXED_FOOTING_SUPERSEDED.json` with an explanatory field. It had the most canonical-looking filename in the directory while pairing refusalness@last with a codeword representation *and* carrying a pre-demeaning permutation p.

### What the verifier said positively, worth recording
The **position finding is stated at its least favourable framing**: on best columns it is 2.0×/4.2×,
but on *median* columns it is 12.6× (`d_surface`) and 51× (refusalness). The headline understates its
own positive result.

### Tick 47 — the provenance guard's demanded rerun landed, and the headline table is regenerating

Job 761697 completed: `refusalness --position last`, **960 rows, `readout_position == "last"` on all
of them, and `readout_token_index == seq_len-1` on all of them.** So the `@last` cell's footing is now
evidenced by an artifact rather than by reading `refusalness.py`. That was the one thing
`analyze_position.py` refused to accept on its first run, and it is the guard doing exactly what the
three dead guards never did — declining to proceed on unverifiable input.

`analyze_position.py` is now regenerating `position_2x2.json` with **all four cells
provenance-checked**. It is slower than expected because the honest version of the interval is
expensive: the `reselect` bootstrap re-argmaxes over every candidate column inside each of 4000
resamples (≈240k regressions), which is the variant that includes the model-selection variance that
two of this sprint's five retractions were about. The cheap `fixed_column` variant is the one I had
been quoting.

Nothing is sent until it finishes. Both reports already carry every audit-6 correction.


## §19 answered directly, and Q2 gets a REPLACEMENT result with the control it lacked

The plan's §19 requires eleven questions answered directly; the full report now has a dedicated section
doing that. Checking them one by one surfaced a genuine gap: **Q2 ("does the final `carrot` become more
`bomb`-like than earlier ones?") had no current answer** — its phase row (P4.3) was RETRACTED and
nothing replaced it.

Computed properly as a within-prompt paired contrast (same prompt, same surface word, only the position
differs), domain-clustered over 6 domains, n=246 doublespeak behavioural prompts:

| L | 4 | 8 | 12 | 16 | 20 | 24 | 31 |
|---|---|---|---|---|---|---|---|
| Δ(final − earlier), doublespeak | −0.025 | −0.082 | −0.090 | **−0.154** | −0.123 | −0.119 | −0.080 |
| t_clustered | −5.0 | −6.2 | −7.1 | **−10.5** | −8.3 | −6.3 | −3.7 |
| p_clustered | 0.004 | 0.002 | 0.001 | **0.0001** | 0.0004 | 0.001 | 0.014 |

**The answer is NO — the final occurrence is LESS on the concept axis, not more**, at every layer.

**And the control is what makes it interpretable.** The same comparison in `benign_literal` — where
there is no bomb meaning at all — gives the **same sign and comparable magnitude** (L16 −0.105,
L31 −0.131, all p < 0.004, n=162). There is no consistent doublespeak-specific excess: at some layers
doublespeak is more negative, at others benign is. **So this is a POSITION effect, not a semantic one:**
the last occurrence of a word sits differently on the axis than earlier occurrences regardless of what
it means.

That control is precisely what the retracted P4.3 claim lacked — it read a within-prompt gradient as
evidence of accumulating concept content without checking whether a prompt with no concept content
shows the same gradient. It does.

This also connects to the sprint's surviving positive finding: **position keeps turning out to matter
more than meaning** on this axis — the predictor×position 2×2 (2–4× effects), and now the
within-prompt occurrence comparison. Both say the codeword's *place* carries more of the measurable
signal than its *sense* does.

### Tick 48 — three hard plan requirements were unmet. Fixed.

Auditing the report against the plan's own §13/§15 text rather than against my memory of it found three
requirements I had not satisfied. None is cosmetic:

1. **§15 specifies the exact path `reports/boombness_objective_sprint_report.md`.** I had written
   `..._full_report.md`. Renamed (via `git mv`, so history follows) and all references updated.
2. **§13 requires a verbatim `Limitations and safety scope` section in every report — I had none.**
   Now present, and it does the thing that section exists for: it scores §13's **six "we found the
   mechanism" criteria explicitly** — **2 met, 3 partial, 1 no** — and states plainly that the correct
   description is a documented correlational finding with a directional null, **not a mechanism**. It
   also records the dual-use scope, that no completion text appears in any report or commit, and that
   only the local open-weight model was attacked (the API is used as a judge, never as a target).
3. **§15 requires 18 numbered contents.** Checked all 18 by keyword: 17 present, **item 8
   (token-level Boombness) missing as its own section** — the Q2 result existed only inside the §19
   answers. Added as §2b, which the plan explicitly wants kept separate from prompt-level.

**And keeping them separate turned out to matter.** Prompt-level Boombness *rises* with demonstrations
(L8 +0.0138 → +0.0449 over k=1→16); token-level, the final occurrence is *lower* on the axis than
earlier ones (−0.154 at L16, p=0.0001) — and the benign control shows the same, so it is positional.
Merged, those two become either one incoherent trend or, worse, a narration like "the codeword
accumulates bombness as the prompt proceeds" that the token-level data directly contradicts. The plan
was right to insist on the separation.

Also added **§15.5, the mandatory tokenization audit** (2352/2352 single-token, 0 ambiguous, 2 distinct
subtoken ids) with the reason it mattered — an earlier bank produced 890/5808 two-subtoken occurrences,
which puts the embedding of `rot` rather than `carrot` at the readout position — and **exact
reproduction commands** for every main run, including the three refusals that are load-bearing and will
stop a reader with wrong inputs.

## §14 SECOND-MODEL REPLICATION — launched on Qwen3-14B (plan requirement, not a nice-to-have)

§14 asks for replication on "one additional open-weight chat model if available". I had been carrying
this as a *suggested next step*, which was wrong — it is in the plan, and one of the six §13 criteria
for claiming a mechanism is **"replicates across prompt families or models"**, which I scored **NO**
partly because of this gap.

**Scope, and why it is partial by necessity.** Refusal directions exist in this repo **only for
Llama** (`refusal_direction_llama_L*.pt`), so the refusalness half of the position 2×2 cannot be
replicated without first fitting refusal directions for Qwen3. What *can* be replicated — and is the
part that is actually ours — is:
1. **G2**: does `d_surface` predict ASR on a second model?
2. **The position effect for `d_surface`**: is the codeword-token localization model-specific?

**The mandatory §2.4 gate first, before any GPU spend.** The bank's targets must be single-token on
the new tokenizer or every per-token comparison is measuring a different vector. Checked:

| model | ` carrot` | ` bomb` | bare `carrot` |
|---|---|---|---|
| Llama-3.1-8B | **1 tok** | **1 tok** | 2 tok (`car`+`rot`) |
| **Qwen3-14B** | **1 tok** | **1 tok** | 2 tok (`car`+`rot`) |
| Phi-4-mini-reasoning | 1 tok | 1 tok | 2 tok |

Full audit on Qwen3: **2352 ok, 0 bad, 0 ambiguous, 0 token-alignment violations** across the same 216
checkable families. The leading-space form the bank was regenerated to guarantee transfers to Qwen3
unchanged — so the bank is reusable and the comparison is legitimate. (Had bare `carrot` been the
form, this would have failed on all three models.)

**Launched:** 761816 (extract @codeword_last), 761817 (extract @last), 761818 (behavioural generation).
Judge follows. Prediction stated in advance so it cannot be fitted afterwards: if the position effect
is a real property of how these models handle a demonstrated codeword, `d_surface` should again be
markedly more ASR-predictive at the codeword token than at the final prompt token. If it is
Llama-specific, that is a limit on the sprint's one surviving positive finding and will be reported as
such.

### Tick 49 — Qwen3 extraction is sane in flight; and a deliberate decision NOT to fit Qwen refusal directions

In-flight numeric check on the Qwen3 `codeword_last` extract (1905 final-occurrence rows so far):
10 `d_surface` cos columns, all non-degenerate (L4 mean −0.443 sd 0.471 → L18 −0.084 sd 0.264),
**0 rows at `seq_len-1`** as required for a codeword readout, `hnorm|L12` ≈ 101 (plausible for a 14B
hidden size). The fit is producing a real direction, not a collapsed one, so the run is worth waiting
for.

**Decision: I am NOT fitting refusal directions for Qwen3, and the reason is circularity, not effort.**
Completing the refusalness half of the position 2×2 on a second model would require a Qwen3 refusal
direction, and the obvious way to get one from material already here is a diff-of-means over the bank's
`direct_harmful` vs `benign_literal` cells. But those are **cells B and A of the very 2×2 the sprint's
directions are built from**. A "refusal" direction fitted on B−A is, up to the context term, the naive
`d_naive` direction this sprint spent its first week showing is confounded — and comparing it against
`d_surface` as a rival predictor would be comparing a direction to a reparameterization of itself.

The Llama refusalness numbers come from **house directions fitted independently of this bank**
(`refusal_direction_llama_L*.pt`), which is what makes them a real rival. Manufacturing a same-bank
substitute for Qwen3 would produce a number that looks like a replication and is not one.

So the second-model replication is scoped to **`d_surface` only** — G2's correlation and the position
effect — and the report will say that the refusalness comparison is Llama-only because no independent
refusal direction exists for Qwen3 in this repo. That is a genuine limit on §13 criterion 6, and it
stays scored **partial** rather than being talked up.

## §14 REPLICATION RESULT #1 — the 2×2 confound REPLICATES on Qwen3-14B; the mid-layer band does NOT

Same bank (sha `71bea179345ed118`, tokenization audit clean on both tokenizers), same script
(`reanalyze_corrected.py`), same C−A contrast, cluster-robust over 6 domains. Qwen3 `lastpos` extract
verified by the self-check: **2352/2352 rows at `seq_len-1`**.

| L | Llama `d_surface` | Llama `d_naive` | ratio | Qwen3 `d_surface` | Qwen3 `d_naive` | ratio |
|---|---|---|---|---|---|---|
| 4 | +0.0230 | +0.0427 | **+1.86** | +0.0057 | +0.0085 | **+1.50** |
| 8 | +0.0272 | +0.0476 | **+1.75** | +0.0210 | +0.0411 | **+1.96** |
| 12 | +0.0154 | +0.0374 | **+2.42** | +0.0255 | +0.0503 | **+1.98** |
| 16 | **−0.0230** | −0.0063 | +0.27 | **+0.0229** | +0.0396 | **+1.73** |
| 18 | **−0.0265** | −0.0106 | +0.40 | **+0.0232** | +0.0388 | **+1.67** |
| 20 | **−0.0293** | −0.0160 | +0.55 | **+0.0219** | +0.0370 | **+1.69** |
| 24 | **−0.0206** | −0.0045 | +0.22 | **+0.0254** | +0.0441 | **+1.74** |
| 31 | +0.0473 | +0.0941 | **+1.99** | +0.0260 | +0.0504 | **+1.94** |

### 1. The sprint's most reusable claim REPLICATES
**The naive direction inflates the effect by ~2× on both models** — Qwen3 ratio 1.50–1.98 with a
**median of 1.74, at every single layer**, against Llama's 1.75–2.42 where the two agree. This is
takeaway #1 (the 2×2 design separates surface from context and quantifies the confound), and it is now
a two-model result rather than a one-model one. It is the strongest thing the sprint has.

### 2. The mid-layer negative band is **Llama-specific**, and that is now doubly established
On Llama, L16–L24 `d_surface` is **negative** (−0.021 to −0.029). On Qwen3 the same layers are
**positive** (+0.022 to +0.025) and the naive direction inflates there exactly as it does everywhere
else. **The sign reversal does not replicate.**

This is the second independent reason to have narrowed that claim. C7 already showed it was absent in
the **behavioural prompts** (present only in semantic/comprehension); now it is also absent on a
**second model**. Both were found after I had written it into a report, and each on its own would have
been sufficient to retract it. Whatever the mid-band reversal is, it is a property of
Llama-3.1-8B on semantic probe prompts, not of doublespeak.

### 3. What survives multiplicity on BOTH models: L31
`holm_rejected` is `{4, 31}` on Llama and `{8, 31}` on Qwen3 — the two models agree only on **L31**,
which is also the layer with the largest effect on both (+0.047 / +0.026) and the dose-independent one
(§8: flat across a 16× demonstration change). The final-layer effect is the representational finding
that is robust to model, to multiplicity, and to demonstration count.

**Consequence for §13 criterion 6 ("replicates across models"):** it moves from **NO** toward
**PARTIAL** — the methodological confound and the L31 effect ⚠(depth-mismatched — see C9) replicate; the mid-layer structure does
not. The ASR-side replication (G2 + the position effect) is still generating on job 761818.

## §14 REPLICATION RESULT #2 — the token-level result replicates on Qwen3, **including its control**

Δ(final occurrence − earlier occurrences) on `d_surface|L|cos`, within prompt, domain-clustered:

| L | Llama doublespeak | p | Llama **benign ctrl** | p | Qwen3 doublespeak | p | Qwen3 **benign ctrl** | p |
|---|---|---|---|---|---|---|---|---|
| 4 | −0.0247 | 0.004 | −0.0315 | 0.000 | −0.0129 | 0.009 | −0.0139 | 0.003 |
| 8 | −0.0819 | 0.002 | −0.0935 | 0.000 | −0.0129 | 0.046 | −0.0230 | 0.001 |
| 12 | −0.0902 | 0.001 | −0.1085 | 0.001 | −0.0211 | 0.019 | −0.0134 | 0.144 |
| 16 | −0.1544 | 0.000 | −0.1051 | 0.001 | −0.0217 | 0.002 | −0.0114 | 0.222 |
| 20 | −0.1225 | 0.000 | −0.0677 | 0.003 | −0.0236 | 0.001 | −0.0172 | 0.067 |
| 24 | −0.1194 | 0.001 | −0.0727 | 0.003 | −0.0649 | 0.000 | −0.0656 | 0.001 |
| 31 | −0.0798 | 0.014 | −0.1313 | 0.003 | −0.0483 | 0.045 | −0.0860 | 0.000 |

(n = 246/162 prompts on Llama, 396/312 on Qwen3.)

**Both halves replicate.** On Qwen3 the final occurrence is again **lower** on the concept axis than
earlier occurrences at every layer, and the **benign control shows the same sign and comparable
magnitude** — at L24 and L31 the benign effect is actually *larger* (−0.0656 vs −0.0649; −0.0860 vs
−0.0483), exactly as on Llama at L31. So the positional reading holds on a second model: **the last
occurrence of a word sits lower on the axis regardless of what the word means.**

Magnitudes are ~3–5× smaller on Qwen3 (−0.013…−0.065 vs −0.025…−0.154), which is worth stating rather
than smoothing over — the *sign and the control pattern* replicate, the effect size does not.

**Why this one matters more than a typical replication:** it is a **negative** finding replicating
*with its control*. The retracted "the later `carrot` becomes more `bomb`-like" claim is now refuted on
two models, and the alternative explanation that replaced it — that this is a position effect, not
concept accumulation — is what holds in both. A negative that replicates is much harder to dismiss
than a positive that does.

**Running tally on §13 criterion 6 (replicates across models):**
| finding | replicates? |
|---|---|
| naive direction inflates ~2× (the 2×2 confound) | **YES** (median 1.74 on Qwen3, every layer) |
| L31 effect survives Holm | **YES** (only layer both models agree on) |
| final-occurrence-is-lower, positional not semantic | **YES**, control included |
| mid-layer (L16–L24) negative band | **NO** — Llama-only, sign flips on Qwen3 |
| G2 correlation / position effect | pending job 761818 (496/960 generated) |

## ☠ CAUGHT BEFORE JUDGING: 92% of the Qwen3 generations were truncated reasoning traces, not answers

A structural check on the Qwen3 generation run before sending it to the judge (tag counts only, no
content read):

| | Qwen3 (thinking default) | Llama baseline |
|---|---|---|
| generations containing `<think>` | **712 / 712 (100%)** | — |
| generations containing `</think>` | **54 / 712 (7.6%)** | — |
| median words | 156 (of a 192-token budget) | 126 |

**So 92.4% of them opened a reasoning block and never closed it** — the model spent the entire
generation budget thinking and produced **no answer at all**. Judging that set would have scored
*truncated reasoning traces* with StrongReject and reported the result as an attack success rate. It is
the same manipulated-≠-measured error as the five retractions, and it would have been the sixth.

**The repo already knew.** `ds_common.apply_template`'s own docstring says: *"Qwen3's default is
thinking-ON, and `enable_thinking=False` must be passed EXPLICITLY."* Prior work in this repo hit this
exact trap. I launched without the flag and got the documented failure.

### Fix, and why the extraction had to be relaunched too
`--enable-thinking {true,false}` is now wired into **both** `extract_boombness.py` and
`score_behavior.py`, because `enable_thinking` changes the **prompt rendering** (Qwen3 injects an empty
`<think>` block into the assistant prefix), not just the sampling. If only generation were re-run, the
representation would be read off a *different prompt* than the one generated from — precisely the defect
behind RETRACTION #2. So both must agree, and both were relaunched:
**762113** (extract @codeword_last), **762114** (extract @last), **762115** (generation), all with
thinking **off**.

### Choice of condition, stated so it is not mistaken for a default
Thinking-**off** is the matched condition: the entire Llama arm is a non-thinking model answering
directly under a 192-token budget, so a like-for-like replication needs Qwen3 answering directly under
the same budget. Thinking-on with a much larger budget is a *different and also interesting* experiment
— it confounds the comparison with reasoning length, so it is not this one.

### Status of the two replication results already recorded
Results #1 (the ~2× confound) and #2 (the token-level occurrence effect) were computed on the
thinking-ON extract. They are internally consistent — every Qwen3 row shares one rendering, and both are
*within-model* contrasts (C−A; final-vs-earlier occurrence) — so they are not invalidated. But they will
be **recomputed on the thinking-off extract** so that every Qwen3 number in the report comes from one
prompt rendering. If either changes materially, the change gets reported.

## ☠ AND THE FIX WAS ITSELF INERT — `--enable-thinking` never reached the generation path

I relaunched with `--enable-thinking false` and checked the output instead of assuming. The thinking-off
run was **structurally identical** to the thinking-on one:

| | thinking-ON run | "thinking-OFF" run |
|---|---|---|
| generations starting with `<think>` at index 0 | 724 / 724 | **112 / 112** |
| median words | 156 | **157** |

**Cause.** `score_behavior.py` templates the prompt **twice, by two different routes**: once for the
readout (`dc.apply_template`, which I patched) and once inside `dc.generate(..., templated=True)`, which
does its *own* templating and takes its *own* `enable_thinking` kwarg (`ds_common.py:997-1006`). I
threaded the flag into the first and not the second, so the argument parsed, appeared in `config.json`
as `"enable_thinking": "false"`, and **did nothing**.

**This is the phantom-cell bug again, exactly:** a flag threaded into one of two paths that must agree,
where the un-threaded path is the one that decides the measurement. Third time this shape has appeared
(`stage_score` position; `readout_position` unread by the analysis; now `dc.generate`).

**What told me the extraction was fine.** The same check that condemned generation exonerated
extraction: mean `seq_len` moved **104.29 → 108.29**, exactly **+4 tokens**, which is the empty
`<think>\n\n</think>\n\n` block the template injects when thinking is off. So the extract runs
(762113/762114) are correct and were kept; only generation was relaunched.

**The guard that now prevents it.** `score_behavior.py` renders a probe prompt **both ways at startup**
and refuses to run unless (a) the two renderings differ at all — otherwise the flag cannot possibly do
anything on this tokenizer — and (b) the rendering it actually gets back matches the mode requested. A
claim about thinking mode is now verified against **the rendered prompt**, not against argparse having
accepted the string. That is the discipline the three dead guards lacked, applied at the point of
failure rather than after it.

Job **762143** is the relaunch.

### The thinking fix now works — and the guard I wrote for it was TAUTOLOGICAL

Job 762143, with `enable_thinking` reaching `dc.generate`:

| | thinking-ON | first "off" attempt (inert) | 762143 (fixed) |
|---|---|---|---|
| generations containing `<think>` | 724/724 (100%) | 112/112 (100%) | **0 / 28 (0%)** |
| median words | 156 | 157 | **44** |

Qwen3 now answers directly, matched to the Llama arm's condition. ASR from this run is a legitimate
measurement of the same object.

**But reviewing my own guard, half of it could never fail.** I had written:

```python
_want = _off if ENABLE_THINKING is False else _on
_got  = dc.apply_template(..., enable_thinking=ENABLE_THINKING)
if _got != _want: raise
```

`_got` and `_want` are **the same call**. That branch is a tautology — the `D_attn == 1` shape this
sprint already retracted, and it would have given false comfort about *precisely* the bug it was
written for, since it verifies the **readout** templating and the bug was in the **generation**
templating. (The other half — refuse if the two modes render identically — is real, and it is what
printed `len 157 vs 138`.)

**Replaced with a check on the OUTPUT, which is what the claim is about:** over the first 24
behavioural completions, if thinking is off and >25% are *unclosed* `<think>` traces, the run aborts
with the specific diagnosis (`dc.generate` templates internally and needs its own kwarg). That check
would have killed the inert run in under a minute instead of after 112 generations. `think_probe` is
initialised unconditionally so the Llama path cannot hit a NameError for a check it does not use.

**Fourth instance of the same shape, and worth naming as a pattern rather than an incident:** a flag
or check threaded into one of two paths that must agree — `stage_score`'s missing `position`,
`readout_position` written but never read, `dc.generate`'s missing `enable_thinking`, and now a guard
that validated the path that was already correct. **The lesson generalises: verify the OUTPUT of the
thing you claim to have changed, never the input you passed.**

## ⚠ C8 — a limitation I found in the POSITION finding itself, while recomputing on the thinking-off extract

### First, the recomputation: results #1 and #2 are unchanged, and there is a reason
Recomputed on the thinking-**off** Qwen3 extract, the confound table is identical to the thinking-on
one to the 4th decimal (ratios min 1.51 / max 1.98 / **median 1.74** either way; `holm_rejected` `{8, 31}`
either way). **Causal masking explains it:** the empty `<think></think>` block is appended to the
*assistant prefix*, which comes **after** the codeword, and a suffix cannot change the representation at
an earlier position. Verified directly — `@codeword_last` cosines are invariant (L8 −0.3291 → −0.3290,
L31 −0.2130 → −0.2129) despite `seq_len` moving 104.29 → 108.29.

That also **predicted** the `@last` readout must differ, and it does, dramatically (thinking-ON L20
+0.982 / L31 +0.967 vs thinking-off −0.043 / −0.124). The thinking-ON `@last` extract is therefore
**unusable** — its final token is the `<think>` control token — and it was never used for anything.

### Now the limitation, which is mine and which weakens the position claim
Checking the fitted **gaps** (the diff-of-means effect size, i.e. how well-determined the direction is
at that position) exposes an asymmetry the position 2×2 does not control for:

| | @codeword_last | @last | ratio |
|---|---|---|---|
| Llama L8 | 6.05 | **0.53** | **11×** |
| Llama L12 | 7.17 | 1.46 | 5× |
| Llama L31 | 45.8 | 40.1 | 1.1× |
| Qwen3 L8 | 74.1 | **2.36** | **31×** |
| Qwen3 L12 | 98.0 | 4.27 | 23× |
| Qwen3 L31 | 468 | 390 | 1.2× |

At the columns the 2×2 actually reports (`L12|proj` @codeword, `L8|proj` @last), the direction is
**13× (Llama) and 41× (Qwen3) better separated at the codeword position.**

**Why this matters.** A low R² at `@last` admits two readings that the design does not separate:
1. the position genuinely carries less ASR-relevant information (**the claim**), or
2. the direction is *worse estimated* there, so the predictor is attenuated by measurement noise (**an artifact**).

There is a defensible argument that (2) *is* (1) — the gap is small precisely because the final prompt
token, a constant template token across all cells, does not separate the conditions — so low
separability is itself the information-content statement. But that argument needs making, not
assuming, and it is not what the report currently says.

**What is NOT affected:** the gaps converge at L31 (1.1× and 1.2×), where both models' effects are
largest and where both survive Holm. So the L31 result does not depend on this asymmetry at all.

**Action:** both reports get this caveat next to the position table, stated as a limitation rather than
buried. The position effect stays reported — it is 2.0×/4.2× and consistent across two probes — but
"the codeword token carries more ASR-predictive signal" must be qualified with "and the direction is
also far better determined there, which this design cannot separate from it."

## §2.6 COMPREHENSION CONTROL — the result exonerates one claim and INDICTS another

The mandatory control the coverage sweep found missing across the whole sprint. Readout is
`comprehension_logodds` = log p("coded") − log p("literal") on `comprehension_usage` rows;
positive = the model still reports the codeword as meaning the coded thing. 60 doublespeak prompts
with ≥1 demonstration, common to all arms, domain-clustered over 6 domains:

| arm | mean logodds | paired Δ vs baseline | t_cl | p | frac still "coded" |
|---|---|---|---|---|---|
| baseline | +0.704 | — | — | — | 0.683 |
| **`d_surface` +0.25** | **+1.347** | **+0.643** | +4.57 | **0.006** | 0.733 |
| **`d_surface` −0.25** | **−0.088** | **−0.792** | −2.77 | **0.040** | **0.500** |
| `random` +0.25 | +1.769 | +1.065 | +6.67 | 0.001 | 0.800 |
| **`d_surface` project_out** | +0.792 | +0.088 | +0.44 | 0.681 | 0.683 |

### 1. The G4 headline is EXONERATED — and it survives the test that could have killed it
`+0.25` **improves** comprehension (+0.643, p=0.006). So when its ASR fell 0.219 → 0.081, the model
understood the codeword mapping **better**, not worse. The alternative reading the missing control left
open — *"the intervention broke comprehension and the refusal is downstream of confusion"* — is
**excluded**. It also makes the refusal story internally coherent: more concept-ness at the codeword →
better recognition of what is being asked → more refusal (0.074 → 0.696).

### 2. The −0.25 arm is INDICTED, and this is exactly what §2.6 exists to catch
`−0.25` **degrades** comprehension to **−0.088** (below zero: the model now prefers "literal"), with
only **50%** of prompts still reporting the coded reading, down from 68%. So its ASR suppression
(0.219 → 0.148) is **at least partly confusion, not mechanism** — and it must not be described as
"removing concept-ness reduces attack success". This is the third independent line on which the two
signs differ, and all three agree:

| | +0.25 | −0.25 |
|---|---|---|
| clears the 4-draw random band | **yes** (p=0.0014) | no (p=0.070) |
| suppresses via refusal | **90.1%** | 0.0% |
| comprehension | **improves** (+0.64) | **degrades** (−0.79) |

### 3. Specificity caveat, stated because it cuts against me
The `random` control raises comprehension **more** than `+0.25` does (+1.065 vs +0.643). So the
comprehension *gain* is not specific to `d_surface` — a norm-matched perturbation at this dose does it
too. What is specific is the **sign asymmetry**: only the negative `d_surface` step degrades
comprehension, and no control does.

### 4. `project_out` — §10.4 arm B, never run before — PRESERVES comprehension exactly
Δ = **+0.088, p = 0.681**, frac coded unchanged at 0.683. Projecting `d_surface` out of L8 leaves the
model's grasp of the mapping intact. **This is the surgical condition the plan actually asked for**, and
the board's earlier claim that §10.3/§10.4-B was "covered by the additive arms" was wrong — an additive
−0.25 step is not a projection removal, and the two behave differently on precisely this measure.

**So the plan's central question (§0.3) is now live for the first time:** does surgical removal reduce
ASR *while* preserving comprehension? Comprehension: preserved. ASR: **launched now** (`projout_beh`).
If ASR drops, §0.3 is met and the sprint has a genuine causal result it did not have an hour ago. If it
does not, that is a cleaner negative than anything G4 produced, because the comprehension confound is
already excluded.

## §10.4 arms C and F are now RUNNABLE — refusal becomes a manipulable object for the first time

The coverage sweep called arm C "the single largest hole in §10", and the reason is sharp: **refusal is
this sprint's conclusion** — the §18 B-vs-C call turns entirely on it — and it had only ever been
**measured, never manipulated**. Two code gaps made the plan's arms unrunnable, so they had been silently
skipped rather than declined:

1. **`--intervene` could express only ONE manipulation.** Three of the plan's six §10.4 arms compose
   two at once. Specs now join with `+` and all hooks apply simultaneously.
2. **The refusal direction was not a manipulable direction at all.** `make_intervention` only knew the
   fitted `d_*` payload plus the random/orthogonal controls. It now accepts `refusalness`, loading the
   **house directions fitted independently of this bank** (`refusal_direction_llama_L*.pt`) at layers
   12/14/16/18/20.

**Why the independence matters, and why I did not take the easy route.** The obvious way to get a
refusal direction from material already here is a diff-of-means over cells `direct_harmful` and
`benign_literal`. But those are cells **B and A of the very 2×2 the sprint's directions come from**, so
such a direction is — up to the context term — a reparameterisation of `d_naive`, the confounded
direction this sprint spent its first week discrediting. Manipulating it and comparing against
`d_surface` would be circular. The house directions were fitted elsewhere, which is what makes them a
real rival.

**Launched** (forward-only comprehension + semantic first, so the §2.6 control exists for these arms too):
- **762181 — arm C:** `refusalness:project_out:18-18:1.0` — remove refusalness.
- **762182 — arm F:** `d_surface:add:8-8:0.25+refusalness:project_out:18-18:1.0` — **add Boombness AND
  remove refusalness.**

**Arm F is the one that matters.** §18=B says Boombness is "mechanistic but not causal". Arm F tests the
alternative that B is a **ceiling effect of refusal**: if adding Boombness does nothing while refusal is
intact, but *does* something once refusal is projected out, then Boombness has a behavioural effect that
refusal was masking — and the label is wrong. If it still does nothing, B is a property of Boombness
rather than an artifact of the refusal ceiling, which is a materially stronger version of the current
conclusion. Either way the label stops resting on an untested assumption.

Also queued behind: `projout_beh` (762169), the ASR half of arm B, whose comprehension is already known
to be preserved.

## §10.4 arms C and F — comprehension intact, so their ASR will be interpretable

Comprehension under intervention, same 60 doublespeak prompts, domain-clustered:

| arm | manipulation | mean | Δ vs baseline | p | frac coded |
|---|---|---|---|---|---|
| baseline | — | +0.704 | — | — | 0.683 |
| `comp_pos` | add Boombness +0.25 | +1.347 | +0.643 | 0.006 | 0.733 |
| `comp_neg` | add Boombness −0.25 | **−0.088** | **−0.792** | 0.040 | **0.500** |
| `comp_projout` | **arm B** remove Boombness | +0.792 | +0.088 | 0.681 | 0.683 |
| `c104_C` | **arm C** remove refusalness | +0.911 | +0.207 | 0.001 | 0.717 |
| `c104_F` | **arm F** add Boombness AND remove refusalness | +1.567 | +0.863 | 0.002 | 0.783 |

**Every arm except `−0.25` preserves or improves comprehension.** So for arms B, C and F the §2.6
precondition is satisfied *before* their ASR is measured — any ASR change they produce cannot be
dismissed as the model having stopped understanding the prompt. That is the position the whole sprint
lacked until today, and it is the difference between "ASR dropped" and "ASR dropped for a reason".

`−0.25` remains the exception and remains disqualified: comprehension goes **below zero** (the model
prefers "literal"), so its ASR suppression is partly confusion.

**ASR launched:** 762187 (arm C), 762188 (arm F). Also running: 762169 (arm B ASR).
**§14:** the Qwen3 thinking-off generations are complete and the judge is running — that is the
behavioural half of the second-model replication.

### What arm F decides
If **adding Boombness with refusal removed** raises ASR above arm C alone, then Boombness *does* have a
behavioural effect and refusal was masking it — **§18 = B is a ceiling artifact and §12 reopens.**
If arm F ≈ arm C, then Boombness has no behavioural effect even with the ceiling lifted, and B becomes a
much stronger claim than it is today. The prediction is recorded here before the numbers exist.

### Tick 53 — arm B is clean on every precondition; its ASR is judging

`projout_beh` (arm B, `d_surface:project_out:8-8:1.0`) finished: **960/960 rows, 0 failures**, and it
passes the coherence gate (uniq 0.712, trigram 0.021, top-word 0.106, truncated 0.43 → OK). Combined
with the comprehension result (Δ = +0.088, **p = 0.681** — unchanged), this arm satisfies **both** §2.6
preconditions *before* its ASR is looked at:

| precondition | arm B status |
|---|---|
| generation not degenerate (coherence gate) | **OK** |
| model still understands the mapping (§2.6 comprehension) | **preserved**, p=0.681 |
| ledger complete (§2.2) | 960 attempted / 960 succeeded / 0 failed |

**This is the first intervention in the sprint to arrive at the ASR question with both controls already
green.** Every earlier arm had at least one problem: α=1 was degenerate (retracted), −0.25 degrades
comprehension, +0.25 improves comprehension but *raises refusal* so its ASR drop has an obvious
alternative explanation. Arm B removes the concept component by projection and changes neither
coherence nor comprehension.

So the §0.3 question — *does surgical removal reduce ASR without destroying comprehension?* — is now a
clean two-outcome test, and the outcomes are recorded here before the judge finishes:

- **If ASR drops:** the sprint has its first genuinely causal result. Removing the concept component
  reduces attack success while the model still understands the prompt and still produces coherent text.
  That is exactly what §0.3 asks for and what G4 failed to deliver, and it would reopen §12 on a much
  better footing than the correlation ever justified.
- **If ASR does not drop:** it is the cleanest negative in the sprint, because the two escape hatches
  are already closed — nobody can say "the intervention broke the model" or "it stopped understanding".
  It would also sharpen §18=B from "steering does not follow the sign" to "the concept component is not
  load-bearing for the behaviour at all".

Judging now. Also running: 762187 (arm C ASR), 762188 (arm F ASR), and the Qwen3 judge (§14's
behavioural half) at 250/960.

## ⚠ C9 — the cross-model "L31 replicates" claim is DEPTH-MISMATCHED. Rerun launched.

The mid-session sweep checked something I never did: **the two models do not have the same number of
layers.**

| model | `num_hidden_layers` | L31 is… |
|---|---|---|
| Llama-3.1-8B-Instruct | **32** | 31/32 = **97% depth — the final block** |
| Qwen3-14B | **40** | 31/40 = **78% depth — a mid-late block** |

I ran Qwen3 with `--layers ...,28,31`, stopping at 31 because that is Llama's last layer. So the
claim *"the L31 effect replicates on Qwen3"* — and the framing of L31 as the layer both models agree
on under Holm — compared **the final layer of one model against a mid-late layer of the other.** The
depth-matched comparison to Llama L31 is Qwen3 **L39** (39/40 = 97.5%), which was never extracted.

**What this does and does not touch:**
- ⛔ **Withdrawn pending the rerun:** "the L31 effect replicates across models", and the claim that L31
  is the layer both models' Holm sets agree on (the index agrees; the *depth* does not).
- ✅ **Unaffected:** the ~2× naive-direction inflation (median 1.74 on Qwen3) holds at **every** layer
  tested, so it does not depend on which layer is final. The token-level occurrence result likewise
  replicates across all tested layers.
- ✅ **Unaffected:** every Llama-only L31 statement — §8's dose-independence, the Holm survival on
  Llama — since those never involved Qwen3.

**Rerun launched (762199):** Qwen3 extraction extended to `--layers 4,8,11,12,16,18,20,24,28,31,34,36,38,39`
with logit-lens layers to 39, thinking-off to match. Once it lands the comparison will be stated in
**relative depth** (Llama 31/32 vs Qwen3 39/40) rather than by raw index, which is the framing that
should have been used from the start.

**Why I missed it:** I treated the layer index as a portable coordinate because both models are
"transformer decoders", and never checked `num_hidden_layers`. Same family as the sprint's other
errors — an implicit assumption of comparability between two things that only *look* like the same
quantity.

## ⛔ §14 RESULT — **G2 DOES NOT REPLICATE on Qwen3-14B.** The pooled ρ agrees; the structure does not.

The second model's behavioural half is in (960 generations, thinking-off verified; 960/960 judged;
`require_done` vetted all three inputs). At first glance it replicates — and that first glance is wrong.

| | Llama-3.1-8B | Qwen3-14B |
|---|---|---|
| n | 234 | 384 |
| pooled ρ (`d_surface|L12|proj`) | **+0.307** | **+0.364** |
| p, i.i.d. | 1.7e-06 | 1.9e-13 |
| p, **CR1 domain-clustered** | **1.2e-03** | **0.206 — NOT significant** |
| p, within-domain permutation | <5e-4 | 5.0e-03 |
| per-domain positive | **6 / 6** | **3 / 6** |
| median per-domain ρ | **+0.282** | **+0.044** |

### Leave-one-domain-out settles it
| dropped domain | Llama ρ | Qwen3 ρ |
|---|---|---|
| city_bridge | +0.309 | +0.438 |
| farm_storage | +0.284 | +0.407 |
| **game_manual** | +0.254 | **+0.015 ← COLLAPSES** |
| instructional | +0.329 | +0.397 |
| lab_safety | +0.327 | +0.386 |
| news_report | +0.320 | +0.415 |

On Llama the association survives dropping any domain (0.254–0.329). **On Qwen3, removing
`game_manual` takes the pooled ρ from +0.364 to +0.015** — one domain of six carries the whole thing,
and three of the other five are *negative* (−0.182, −0.126, −0.071).

**So the matching pooled ρ was a coincidence, and quoting it as replication would have been a Simpson's-
paradox artifact of exactly the kind this sprint retracted twice.** It is also why the CR1 clustered p
(0.206), which treats domains as the unit, disagrees so sharply with the i.i.d. p (1.9e-13): the
i.i.d. figure is counting 384 prompts as 384 independent observations of an effect that exists in one
domain.

### What this does to the sprint's standing claims
| claim | replicates on Qwen3? |
|---|---|
| the 2×2 confound: naive direction inflates ~2× | **YES** — median 1.74, at every layer |
| token-level: final occurrence is *lower*, positionally not semantically | **YES**, control included |
| **G2: Boombness predicts ASR** | **NO** — pooled only, carried by 1 of 6 domains |
| L31 effect | **withdrawn** (C9: depth-mismatched, rerun 762199 in flight) |
| mid-layer negative band | **NO** (already known) |

**G2 was the sprint's main positive correlational result, and it is now single-model.** The honest
statement is: *Boombness predicts attack success in Llama-3.1-8B robustly across domains; in Qwen3-14B
the same measurement is not a domain-general association.* The methodological contribution — the 2×2 and
the confound it quantifies — is what replicates, which is consistent with it being the sturdiest thing
here all along.

**§13 criterion 6 ("replicates across prompt families or models") stays scored NO for the causal claim
and becomes PARTIAL overall**: the design and two structural findings port; the headline correlation does
not. Both reports will carry this table.

## ✅ C9 RESOLVED — at matched DEPTH the final-layer effect replicates cleanly (better than I had claimed)

Job 762199 extracted Qwen3 to its true final layers. The depth-matched comparison:

| | layer | relative depth | `d_surface` (C−A) | Holm |
|---|---|---|---|---|
| **Llama-3.1-8B** | L31 | 31/32 = **97%** | **+0.0473** | **True** |
| **Qwen3-14B** | **L39** | 39/40 = **98%** | **+0.0521** | **True** |
| Qwen3-14B | L31 | 31/40 = 78% | +0.0261 | True |

**The effect replicates at matched depth, and my error had UNDERSTATED it.** Comparing Llama's final
layer to Qwen3's 78%-depth layer gave +0.047 vs +0.026 (about half); comparing final to final gives
**+0.047 vs +0.052 — nearly identical, both Holm-significant.** The withdrawn claim comes back stronger
than it was, stated in relative depth this time.

The Qwen3 depth profile also shows why the index mattered: `d_surface` runs +0.021…+0.026 across the
middle (L8–L31) and then rises to **+0.052 at L39**, so the final-layer spike is a real feature that
stopping at L31 simply missed. The ~2× naive inflation holds throughout (1.51–1.98, median ~1.8).

**Restated claim:** *the final-layer effect is the sprint's most robust representational finding — it is
the largest effect in both models, survives Holm in both, is dose-independent (§8), and replicates at
matched relative depth (97% vs 98%).*

## ⛔ C10 — the comprehension story is NOT axis-specific. My specificity claim FAILS.

I said: *"only the negative `d_surface` step degrades comprehension, and no control does."* That claim
had never been tested, because **no negative random control existed**. I ran one (762200):

| arm | Δ comprehension | p | frac coded |
|---|---|---|---|
| `d_surface` **+0.25** | +0.643 | 0.006 | 0.733 |
| **random +0.25** | **+1.065** | 0.001 | 0.800 |
| `d_surface` **−0.25** | −0.792 | 0.040 | 0.500 |
| **random −0.25** | **−1.470** | 0.004 | **0.383** |
| **`project_out`** | **+0.088** | **0.681** | 0.683 |

**The pattern is driven by the SIGN OF THE DOSE, not by the axis.** A positive step raises p(coded) and a
negative step lowers it — for `d_surface` *and* for a norm-matched random direction — and the random
control moves comprehension **further in both directions** (+1.07 vs +0.64; −1.47 vs −0.79). The paired
contrast is +0.678 (t_cl=+3.38, **p=0.020**) in the direction of `d_surface` perturbing comprehension
**LESS** than random.

### What this retracts, and what survives
- ⛔ **Retracted:** "the sign asymmetry in comprehension is specific to `d_surface`", and the
  three-line agreement table whose third row was "comprehension: improves / degrades". Comprehension
  does **not** discriminate `d_surface` from a random perturbation, so that table has **two** lines
  (band clearance z=−3.2 vs −1.8; refusal route 90.1% vs 0.0%), not three.
- ✅ **Survives:** the +0.25 exoneration, in its narrow and originally intended form — comprehension did
  **not** degrade under +0.25, so "the ASR drop is confusion" is still excluded for that arm. That was
  always the load-bearing claim; the specificity gloss I added on top of it was not.
- ✅ **Strengthened:** `project_out` (arm B) is now the *only* intervention of five that leaves
  comprehension unchanged (+0.088, p=0.681) while all four additive arms move it by 0.6–1.5. That makes
  it the genuinely surgical condition, and makes its pending ASR the cleanest test in the sprint.

### A near-miss worth recording
The first run of this test returned **byte-identical numbers for `comp_rand` and `comp_rand_neg`**, which
is impossible for two different doses. Cause: my analysis globbed `comp_rand_*`, which also matches
`comp_rand_neg_*`, and `sorted()[-1]` picked the *neg* directory — **I compared the control against
itself** and briefly "confirmed" the opposite conclusion. Caught only because identical values are
implausible. Fixed by matching `<tag>_2026*`. This is the *fifth* instance of the sprint's signature bug:
selecting a thing by an incidental property (here a name prefix) rather than by identity.

## ⛔ RETRACTION #6 — the §11 "role framing does not move Boombness" TIGHT NULL is WRONG, and inverted

The recompute found that my arithmetic was right and my **error term** was wrong.

| analysis | L12 result |
|---|---|
| naive one-way ANOVA (as reported) | F(5,810)=**0.175**, p=**0.972** — reproduces exactly |
| blocked on domain | F=0.178, p=0.971 (domain is balanced — a red herring) |
| blocked on **query_kind** | F=**2.81**, p=**0.016** — already breaks the null |
| **paired within-stem** (the design is perfectly crossed: 72 complete 6-style stems) | **F(5,355)=20.30, p=8.1e-18**, permutation p<5e-5, **11/15 pairwise differences survive Bonferroni** |

**And the "3.6% of the within-style sd" statistic is a variance-decomposition error.** The denominator I
used (0.1098) is almost entirely *between-stem* variance — different domains, demo counts, query kinds —
which the paired design removes. The correct within-stem residual sd is **0.0082**, a **14× smaller**
error term. Against it the style-mean spread is **53.1%, not 3.6%.**

**A worse structural problem underneath it.** In that 816-row pool, `plain` and the five role styles
occupy **disjoint `bank_block`s**: `plain` is effectively *the rest of the bank* (240 core2x2 + 72
consistency + 72 families + 48 strength + 24 position rows), carrying four query kinds and
`n_examples ∈ {1,2,4,8,16}`, while each role style has 72 rows, two query kinds and `n_examples ∈ {2,4,8}`.
Family-id overlap between the matched-plain arm and the role arm is **zero**. So the report's sentence
that content, domain, demo count and query were *"held fixed"* is **FALSE for the analysis I ran** — it is
true only inside the 72 complete stems, which is exactly the analysis I did not do.

### Corrected §11 answer
**Role framing DOES move Boombness — systematically and reliably, but by a small amount.** Within-stem
F=20.30 (p=8e-18) with 11/15 pairwise gaps surviving Bonferroni; largest pairwise gap **0.0116**, which
is **4.1% of the grand mean** at L12. So the honest statement is *"a small, highly reliable effect"*, not
*"a tight null"* — the opposite of what both reports say. §19 Q8 ("do user-like/CoT-like framings increase
Boombness?") flips from **No** to **Yes, by a little, reliably.**

## ⛔ RETRACTION #7 — the "4-draw random-control band" was n=1. My own fix to an audit finding was a no-op.

Audit item A4-4 said "more than a random direction" rested on a single draw. I launched four seeds
(20260817–20260820), reported a band of mean −0.0366 with between-draw sd 0.0049, and concluded
**"+0.25 clears the band, t=−3.23, p=0.0014"**. Verified today:

| the four "independent draws" | completions sha256 |
|---|---|
| s20260817 / s20260818 / s20260819 / s20260820 | **e4a15fcb ×4 — identical** |

The only field differing between the four runs is `arm`, the label. Cause:
`make_intervention` seeded the control direction from the **literal** `20260816 + L`, so `--seed` never
reached it; the direction was identical, generation is greedy, and the completions came out byte-for-byte
the same. **The "between-draw sd" of 0.0049 was judge noise on ONE generation set**, and the band was
n=1 wearing an n=4 label.

⛔ **Withdrawn:** the 4-draw band, the p=0.0014 "clears the band" verdict, and the claim that A4-4 was
resolved. The earlier *paired contrasts* against the two original single-draw controls are unaffected
(+0.25 vs random z=−3.6; −0.25 z≈−2.1) — but those were always single-draw, which is what A4-4 objected
to in the first place.

**Fixed:** `--seed` now reaches the control direction (`control_seed`), proven by construction —
cos(seed17, seed18) = **+0.019**, where before it was exactly 1.0. Four genuinely independent draws
relaunched with seeds 20260901–04.

**This is the fourth "fix that did nothing" in this sprint** — after the coherence gate that never
matched, the dynamic-range check that compared against a null control, and `--enable-thinking` reaching
only one of two paths. The pattern is now unmistakable: **I keep verifying that a fix was applied rather
than that it changed the measured object.** Every remaining guard in this codebase should be assumed
inert until someone constructs its failure case.

## ★ §0.3 ANSWERED — removing Boombness **RAISES** ASR. The sign is opposite to the hypothesis.

Arm B (`d_surface:project_out:8-8:1.0`) is the first intervention to reach the ASR question with every
precondition green: coherence **OK**, comprehension **unchanged** (Δ +0.088, p=0.681), ledger 960/960/0.
Common 270-prompt set, all arms coherence-gated:

| arm | ASR | 95% CI | refusal | paired Δ vs baseline |
|---|---|---|---|---|
| baseline | 0.219 | [0.173, 0.272] | 0.074 | — |
| **arm B — remove Boombness (project_out)** | **0.300** | [0.248, 0.357] | **0.074** | **+0.0736 ± 0.0248** |
| random +0.25 | 0.178 | [0.137, 0.228] | 0.085 | −0.0352 |
| orthogonal +0.25 | 0.189 | [0.147, 0.240] | 0.093 | −0.0306 |
| add Boombness +0.25 | 0.081 | [0.054, 0.120] | **0.696** | −0.1144 |

Domain-clustered contrasts (6 domains) — and the clustering matters, so both are stated:

| contrast | Δ | t_cl | **p_cl** |
|---|---|---|---|
| arm B − **random** control | **+0.1088** | +3.15 | **0.025** |
| arm B − **orthogonal** control | **+0.1042** | +3.37 | **0.020** |
| arm B − add-Boombness(+0.25) | +0.1880 | +6.20 | **0.0016** |
| arm B − baseline | +0.0736 | +1.89 | **0.117 — not significant** |

### The answer to §0.3, stated plainly
**No — surgical removal does not reduce ASR. It INCREASES it.** And the increase is significant against
both **norm-matched perturbation controls** (p=0.020–0.025), which themselves *lower* ASR slightly, while
the bare vs-baseline contrast is **p=0.117** under domain clustering (n=6 clusters is few; the naive
z is +2.97). So the directional effect is visible **only against controls**, and that is how it must be
quoted.

### Why this is the sprint's first genuinely causal result
Every precondition the plan demanded is satisfied *simultaneously*, which no earlier arm managed:
coherence preserved, comprehension preserved (p=0.68), refusal **unchanged** (0.074 → 0.074), and a
directional ASR change that exceeds norm-matched controls. The α=1 arm was degenerate; −0.25 degrades
comprehension; +0.25 confounds with a refusal spike.

### And it inverts the sprint's guiding hypothesis
The plan assumed doublespeak works by *smuggling concept content in*, so **more** Boombness should mean a
stronger attack. Every arm now says the reverse, coherently:

| manipulation | concept-ness at codeword | refusal | ASR |
|---|---|---|---|
| **+0.25** (add) | higher | **0.074 → 0.696** | **0.219 → 0.081** |
| **project_out** (remove) | lower | 0.074 → 0.074 | **0.219 → 0.300** |

**Boombness at the codeword behaves as a DETECTION signal for the safety mechanism, not as a driver of
compliance.** Raising it makes the request legible and refusal fires; removing it makes the request less
legible and the attack succeeds more. That is why the correlation was positive within the attack arm and
yet steering "the wrong way" — the correlation was reading a *detectability* gradient.

### Consequence for §12, which reopens with the sign flipped
An objective built on this axis should **MINIMISE** the projection, not maximise it. The plan's §12.1
("pure Boombness objective", maximise) is the wrong sign; the runnable version is a *minimisation*
objective, and `project_out` is its idealised limit. **This is a new, testable direction the sprint did
not have an hour ago.**

⚠ **Required before anyone builds on this:** the vs-baseline contrast is p=0.117 clustered, so this needs
(a) replication on a second concept pair, (b) a projection dose–response (α<1 partial removal), and
(c) the same arm on Qwen3 — especially given G2 did not replicate there. It is a strong, clean signal,
not yet a settled fact.

## ★ ARM C — removing refusal ENTIRELY does not help the attack. Refusal is not the binding constraint.

| arm | ASR | refusal | Δ vs baseline | t_cl | p_cl |
|---|---|---|---|---|---|
| baseline | 0.219 | 0.074 | — | — | — |
| **arm C — remove refusalness** | **0.226** | **0.000** | **−0.013** | −0.86 | **0.431** |
| arm B — remove Boombness | 0.300 | 0.074 | +0.074 | +1.89 | 0.117 |
| add Boombness +0.25 | 0.081 | 0.696 | −0.114 | −5.99 | 0.0019 |
| random +0.25 | 0.178 | 0.085 | −0.035 | −3.33 | 0.021 |

**The manipulation worked and the behaviour did not follow.** Projecting out the refusal direction drives
the refusal rate from 0.074 to **exactly 0.000** — every keyword refusal is gone — and ASR moves by
**−0.013 (p=0.431), i.e. not at all.**

### Why this matters more than it looks
The doublespeak attack has *already* suppressed refusal to 7.4%. So there was almost nothing left for arm
C to remove, and removing it buys nothing: **refusal is not the binding constraint on attack success
inside this arm.** That is a direct measurement of something the sprint had only ever inferred from
between-arm comparisons.

### And it reorders the two candidate explanations
| contrast | Δ | t_cl | p_cl |
|---|---|---|---|
| **arm C − arm B** (remove refusal vs remove Boombness) | **−0.087** | −2.84 | **0.036** |

**Removing Boombness helps the attack significantly MORE than removing refusal entirely does.** Within
the doublespeak arm, the concept-detectability axis is doing more work than the refusal direction.

**Consequence for §18.** Outcome **C** ("ASR is mainly explained by refusal suppression") is now
*directly* contradicted for the within-arm case: refusal can be driven to zero with no ASR gain. The
between-arm story (direct 96% refusal → doublespeak 7%) still stands — refusal suppression is how the
attack *gets started* — but it does not explain variation in success *once inside* the attack. Label C is
weakened by a manipulation, not by a ratio contest.

### Arm F is the discriminating test, and the prediction is recorded before its judge finishes
Arm F = **add Boombness AND remove refusalness**. The +0.25 arm's ASR collapse (0.219 → 0.081) was
attributed to *triggering refusal* (90.1% of its suppressed prompts were refusals). Arm F removes that
route:
- **If the suppression really was refusal:** with refusal projected out, arm F's ASR should return to
  ≈ baseline or above (0.22–0.30).
- **If suppression works by some other route:** arm F's ASR should stay low (≈ 0.08) even with refusal
  gone — and the refusal explanation of the +0.25 arm would be wrong.

Arm F's judge is at 381/960. Four genuinely independent control-band draws (verified: 4 distinct
completion sets, 81–85% pairwise disagreement) are queued behind it.
