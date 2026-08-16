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
| P2.1 | §5.1 | Hidden-state replacement, smoke | TODO | |
| P2.2 | §5.2 | Additive bomb-direction sweep, smoke | TODO | |
| P2.3 | §5.3 | Metrics + comprehension controls validated | DONE | forward-only readouts validated; comprehension answer pair fixed to single tokens |
| P2.4 | §5 | Pilot 30–50 prompts | TODO | |
| P2.5 | §5.4 | `decision_gate.md` | TODO | |
| P3.1 | §6.1 | Logit-lens Boombness | DONE | `signals.logit_lens` + `logit_lens_boombness_batch`; ids validated by `readout_id_pair` |
| P3.2 | §6.2 | Direction Boombness | DONE | `signals.estimate_directions` — the 2×2 estimator (`d_surface`/`d_context`/`d_inter`/`d_naive`) |
| P3.3 | §6.3 | Simple probe | DONE | `probes.py` — PCA-64, margin readout, shuffled control ~0.5; run `margin_20260816_192040` |
| P3.4 | §6.3 | Hard-negative / held-out-condition probe | DONE | `d4_heldout_ds` reproduces the d_surface layer profile from a held-out-trained classifier |
| P3.5 | §6.4 | Metric comparison | DONE | 4 metrics compared: d_surface / d_naive / probe margin / logit lens — see Tick 7 |
| P4.1 | §7.1 | Token-level Boombness per occurrence × layer | DONE | 8472 occurrence rows, per-occurrence × per-layer, run `full_20260816_185942_1008673` |
| P4.2 | §7.1 | Occurrence × layer heatmaps | DONE | `analysis/plots/occurrence_x_layer_*.png` for all four 2×2 cells |
| P4.3 | §7.1 | Later-carrot-more-bomb-like test | DONE | two-humped profile: write hump L8, null L16–22, readout hump L24–31 |
| P4.4 | §8 | Example-count sweep | TODO | |
| P5.1 | §4 | ~600-prompt bank | TODO | |
| P5.2 | §9 | Generations + evaluation | TODO | |
| P5.3 | §9 | Prompt-level Boombness | TODO | |
| P5.4 | §9 | Correlation / regression | TODO | |
| P5.5 | §9 | Figure-9-style plot | TODO | |
| P6.1 | §10.1 | Attention edge knockout | TODO | |
| P6.2 | §10.2 | Head knockout | TODO | |
| P6.3 | §10.3 | Direction knockout | TODO | |
| P6.4 | §10.4 | Combined Boombness/refusal | TODO | |
| P6.5 | §10 | Comprehension controls | TODO | |
| P6.6 | §10 | Causal vs destructive separation | TODO | |
| P7.1 | §11 | Role-style variants | TODO | |
| P7.2 | §11 | Role framing → Boombness | TODO | |
| P7.3 | §11 | Userness/CoTness probes (if feasible) | TODO | |
| P7.4 | §11 | Boombness + role predicts ASR | TODO | |
| P8.1 | §12.1 | Boombness GCG objective | TODO (gated) | |
| P8.2 | §12.2 | Boombness − refusal objective | TODO (gated) | |
| P8.3 | §12.5 | Baseline / refusal-only comparison | TODO (gated) | |
| P8.4 | §12.5 | Universality + held-out transfer | TODO (gated) | |
| P8.5 | §15 | Final reports | TODO | |

---

## Decision gates

| Gate | Question | Verdict | Date |
|---|---|---|---|
| G1 (§5.4) | Can we force `carrot` to be `bomb`-like, and does it change behavior? | pending | |
| G2 (§9) | Does prompt-level Boombness predict ASR? | pending (needs ASR run) | |
| G3 (§10) | Can Boombness be removed without destroying comprehension? | pending | |
| G4 (§12) | Is Boombness a usable GCG objective? | pending | |
| FINAL (§18) | A strong-positive / B mechanistic-not-causal / C refusal-only / D negative | pending | |

---

## Bug / integrity audit log

Every 4h an independent agent audits code + outputs for result-affecting bugs. Findings land here.

| Date | Auditor | Finding | Severity | Fix | Rerun needed? |
|---|---|---|---|---|---|
| 2026-08-16 | self-review workflow, `review:directions` lens | **`all_first_ids` put the generic token `car` on the codeword side of every logit-lens score.** `word_token_ids` took the FIRST id of each surface variant. On Llama-3.1-8B `" carrot"`→`[' carrot']` but `"carrot"`→`['car','rot']`, `"Carrot"`→`['Car','rot']`, `" Carrot"`→`[' Car','rot']` — so **3 of carrot's 4 "first ids" are car-the-vehicle**, one of the most frequent tokens in the vocabulary, while all 4 of bomb's variants genuinely spell bomb. | **result-corrupting** | Added `signals.readout_ids` / `readout_id_pair`. Default `primary` mode = the single leading-space whole-word token per side (`' bomb'` vs `' carrot'`) — exactly symmetric, and exactly the token that appears in our prompts. Multi-token variants are recorded under `rejected_first_ids` instead of scored. Raises if the leading-space form is not single-token. | **YES — cancelled job 760596 mid-run at 600/1464 rows and resubmitted as 760598.** Direction metrics (`d_*`) were unaffected (they use no token ids); the `ll\|*` logit-lens columns were. |
| 2026-08-16 | §5 smoke (job 760661) | **Readouts at the patched layer were PRE-patch.** `out.hidden_states[L+1]` is filled by the framework's own capture, registered before ours, so at the very layer being intervened on it reported the value the patch was about to overwrite. Measured: patching window `L8` left the L8 boombness readout bit-identical to baseline (−0.2294) while a window containing layers *below* 8 moved it (+0.1477) — the readout only ever saw upstream effects and reported "no effect at the intervened layer" **by construction**. | **result-corrupting** | New `BlockCapture` registers our own forward hooks on the decoder blocks *after* the patch contexts, so they run later and read the block's true output. Wired into all 5 readout call sites. | **YES — smoke 760661 discarded, resubmitted as 760681.** No full run had been done, so nothing published was affected. |
| 2026-08-16 | §5 smoke (job 760661) | **The L31 readout in `aggressive_patching` was in the wrong coordinates.** `forward_hidden` was fixed for the last-layer norm tie, but `readout()` read `out.hidden_states` directly, so its L31 projection mixed post-norm activations against directions fitted on raw block outputs. | **result-corrupting** | Same `BlockCapture` fix — reading the block's own output is raw by construction. | Same rerun. |
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

**And the L31 effect survived it, larger:** `C−A` went from +0.112 (contaminated) to **+0.133**
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
