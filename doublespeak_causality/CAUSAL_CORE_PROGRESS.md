# Causal Core — Progress Tracker

**Live status doc for [`CAUSAL_CORE_PLAN.md`](CAUSAL_CORE_PLAN.md).** This is the single place to see what
has been executed, what is running, and what the numbers are. Updated every iteration (loop cadence 30 min).

States: `NOT_RUN` · `RUNNING` · `PARTIAL` · `BLOCKED` · `FAILED` · `COMPLETE`

Branch: `behavioral-causality-sprint` · Started: 2026-07-29

---

## Status board

| ID | Stage (plan ref) | Status | Evidence / notes |
|----|------------------|--------|------------------|
| S0 | Audit & freeze prior results; fix overclaims (§16.1–2) | `NOT_RUN` | |
| S1 | Phase A: fixed-pair CARROT↔BOMB semantic benchmark (§3, §16.3) | ✅ `COMPLETE` | `data/pair_benchmark/pair_carrot_bomb.json` — 800 semantic + 900 behavioral prompts, 60 paraphrases, **0 skipped**, 21/21 tests pass |
| S2 | Readout validation: Direct+ / Neutral− controls (§16.4) | ✅ **COMPLETE — GATE PASSED per-cell** | full run 693557 (800 prompts). **17/30 (readout × demo-style) cells usable.** On usable cells: `DS − Neutral` reads-as-concept **+0.500 [+0.393, +0.607]**, p_concept **+0.307 [+0.249, +0.367]**, n=84. |
| S3 | Rep extraction: layers × positions × components (§16.5) | ✅ `COMPLETE` ×2 | jobs 693558 (`cloze`) / 693559 (`one_word`); 160 rows each, **256 cells, 0 missing position cells**, 4 components × 4 positions × 32 layers |
| S4 | Cross-fitted `d_Direct` / `d_DS` + subspaces (§2, §16.6) | ✅ `COMPLETE` ×2 | 160 directions + 64 PCA subspaces per readout |
| S5 | Intervention sweeps add/remove/replace (§4, §16.7) | `RUNNING` | jobs 693570 (`cloze`) / 693571 (`one_word`), `--mode layer_scan`, α∈{1,2}, all 32 layers, cross-fitted |
| S6 | Dose-response + ≥20 matched controls (§4.5, §5, §16.8) | `NOT_RUN` | code ready: `--mode dose` / `--mode controls` |
| S7 | Held-out paraphrase confirmation (§14, §16.9) | `NOT_RUN` | cross-fitting is ON by default in `34`; Holm correction wired in `35` |
| S8 | Attention knockout + attn-vs-MLP patching (§6, §16.10) | `NOT_RUN` | |
| S9 | Causal attack-window estimate (§16.11) | `NOT_RUN` | |
| S10 | Causal objective terms, each intervention-validated (§7, §16.12) | `NOT_RUN` | |
| S11 | Continuous soft-prompt positive control (§8.5, §16.13) | `NOT_RUN` | |
| S12 | Demonstration-level GCG/MAC — gated on S11 (§8.6, §16.14) | `NOT_RUN` | |
| S13 | Codeword properties incl. embedding distance (§8.1, §16.15) | `NOT_RUN` | |
| S14 | Qwen3 thinking on the fixed pair (§G, §16.16) | `NOT_RUN` | |
| S15 | DeepSeek tokenizer localization + regression tests (§16.17) | `NOT_RUN` | |
| S16 | Scale ≥10 pairs + replication — gated (§F, §16.18) | `NOT_RUN` | |
| S17 | Documentation / registry / job tables (§15, §16.19) | `RUNNING` | this file created |

---

## Gates (do not skip; the plan's ordering is load-bearing)

1. **S2 gate** — no intervention result is interpretable until every readout separates `DIRECT_BOMB` from
   `NEUTRAL_CARROT`. If a readout fails, fix the readout, do not reinterpret the intervention.
2. **S7 gate** — headline layer/α are chosen on *dev* paraphrases and confirmed on *held-out* paraphrases,
   with multiple-comparison correction over the layer×α grid.
3. **S11 gate** — discrete optimization (S12) starts **only** if continuous optimization can move the causal
   score. If it cannot, debug the objective (S10), do not run GCG.
4. **S16 gate** — scale-up starts **only** after the fixed-pair causal chain (S1→S9) passes.

## Honest-reporting rules in force (§15)

Never convert decoding→behavior, correlation→causality, representation loss→ASR, one optimizer failure→
impossibility, or one pair→a general mechanism. Harmful text stays in the main process / SLURM; subagents
receive only redacted labels, scalars and statistics.

---

## SLURM jobs

| Job ID | Stage | Script | Node | Submitted | Status | Output dir |
|--------|-------|--------|------|-----------|--------|------------|
| 693551 | S2 smoke | `run_pair_readout.sh` | — | 2026-07-29 | CANCELLED (unstratified `--limit` made the gate vacuous) | — |
| 693555 | S2 smoke | `run_pair_readout.sh` `DSLIMIT=80` | n-803 | 2026-07-29 | ✅ COMPLETE — gate passed | `outputs/pair_readout_Llama-3.1-8B-Instruct_20260729_215216_693555` |
| 693557 | S2 full | `run_pair_readout.sh` (all 800) | n-802 | 2026-07-29 | ✅ COMPLETE — per-cell gate | `outputs/pair_readout_Llama-3.1-8B-Instruct_20260729_220059_693557` |
| 693558 | S3 `cloze` | `run_pair_reps.sh` | — | 2026-07-29 | ✅ COMPLETE | `outputs/pair_reps_*_693558` |
| 693559 | S3 `one_word` | `run_pair_reps.sh` | — | 2026-07-29 | ✅ COMPLETE | `outputs/pair_reps_*_693559` |
| — | S4 `cloze` | `33_build_directions.py` (CPU) | login | 2026-07-29 | ✅ COMPLETE | `outputs/pair_directions_20260729_215640_299312` |
| — | S4 `one_word` | `33_build_directions.py` (CPU) | login | 2026-07-29 | ✅ COMPLETE | `outputs/pair_directions_20260729_215701_299521` |
| 693570 | S5 layer_scan `cloze` | `run_pair_interv.sh` | — | 2026-07-29 | RUNNING | `outputs/pair_interv_layer_scan_*_693570` |
| 693571 | S5 layer_scan `one_word` | `run_pair_interv.sh` | — | 2026-07-29 | RUNNING | `outputs/pair_interv_layer_scan_*_693571` |

---

## Iteration log

### ITER0 — 2026-07-29 — setup
- Read `CAUSAL_CORE_PLAN.md`; confirmed nothing in it had been executed (plan file was untracked).
- Verified repo state: `HEAD = 1f328d8` on `behavioral-causality-sprint`, in sync with origin, clean apart
  from the new plan file. Prior sprint (`f408d71` and earlier) is an ancestor — nothing lost.
- Environment: SLURM `killable` partition reachable, L40S nodes `n-801..805`/`t-806` present; no jobs of
  ours queued; conda env `poc_stage2` present.
- Created this tracker + an 18-item task list mirroring plan §16.
- Launched a read-only recon fan-out over the reusable code (patching, benchmark, readouts, attention,
  optimization, stats/SLURM) so new code is written as thin glue over existing machinery.

### ITER1 — 2026-07-29 — S1 complete, S2 submitted, S3–S7 code landed
**New code (all thin glue over existing machinery):**
- `30_build_pair_benchmark.py` — the fixed-pair benchmark. 8 structurally matched
  conditions (`DIRECT_CONCEPT`, `NEUTRAL_CODEWORD`, `DOUBLESPEAK`, `BENIGN_REMAP`,
  `UNRELATED_TARGET`, `REPEATED_CODEWORD`, + two no-demo baselines) × 5 demo styles ×
  {4,8,12} demos × 5 readouts × immutable dev/heldout. Every condition carries a demo
  block of the same size, so **prompt length is not a confound**, and the dev/heldout
  demonstration pools are **text-disjoint**, so a direction fitted on one split is
  tested on sentences it has never seen.
- `31_validate_readouts.py` + `slurm/run_pair_readout.sh` — the S2 gate.
- `pair_common.py` — component capture (`resid_pre`/`attn_out`/`mlp_out`/`resid_post`),
  position resolution on templated text, a **forward-only** semantic score (≈10× cheaper
  than generation — this is what makes the exhaustive sweeps affordable), and the §5
  control-vector builders (norm-matched, orthogonal, in-PCA-subspace).
- `32_extract_pair_reps.py`, `33_build_directions.py`, `34_intervention_sweep.py`,
  `35_analyze_pair_causal.py` — S3→S7.
- `tests/test_pair_benchmark.py` — 21 GPU-free tests; 29 pass across the suite.

**Two real bugs found and fixed while building:**
1. `ds_common.git_commit()` returned `"unknown"` whenever `git` was not on PATH (it lives
   in the *base* conda env, not `poc_stage2`), silently degrading the §15 provenance
   record. Now falls back to reading `.git/HEAD`.
2. The demo pools were filtered with a `\bword\b` regex, which drops every plural. The
   remapped control conditions silently lost ~25% of their demonstrations, leaving the
   conditions unbalanced (99 skipped cells). Pools are now pre-filtered for substitution
   survival; the builder asserts `n_skipped == 0` and equal cell counts.

**Deliberate methodological upgrades over the prior sprint:**
- Multiple-comparison correction (Holm–Bonferroni) is wired into `35` over the
  layer × α grid. The recon confirmed `stats.holm_bonferroni` existed but was **never
  called** anywhere in the project.
- Controls are reported as a **distribution** (≥20 draws, three families, percentile and
  z of the concept-specific arm within it), never a single seed.
- Cross-fitting is the default: a `dev` prompt is intervened with the `heldout`
  direction and vice versa.

### ITER2 — 2026-07-29 — S2 gate PASSED, S3+S4 complete, S5 running

**S2 gate (job 693555, n=80 stratified smoke) — PASSED.** Four of five safe semantic
readouts separate the controls *perfectly*:

| readout | `DIRECT_CONCEPT` reads-as-concept | `NEUTRAL_CODEWORD` reads-as-concept | gate |
|---|---|---|---|
| `cloze` | 1.00 | 0.00 | PASS |
| `one_word` | 1.00 | 0.00 | PASS |
| `forced_choice` | 1.00 | 0.00 | PASS |
| `repeat_concept` | 1.00 | 0.00 | PASS |
| `repeated_codeword` | 0.00 | 0.00 | FAIL (by construction — free continuation, not a label; score it by probability mass instead) |

**The hijack is already measurable, paired and CI-backed, at n=10 matched cells:**
`DS − Neutral` on `p_concept` = **+0.150 [+0.062, +0.243]** (CI excludes 0).

**New finding — the hijack is READOUT-DEPENDENT.** Under `cloze` ("…*carrot* refers to
____") the model *states* the hijacked meaning (DS reads-as-concept 1.00, p_concept
0.368). Under `one_word` ("what does *carrot* refer to?") it answers literally
(reads-as-codeword 1.00) even though the probability mass on the concept still rises
(0.0000 → 0.124). So the hijacked meaning is present but only *surfaces* under some
probes. This matters methodologically: a single readout can make the effect look absent.
Both readouts are carried through the whole causal chain from here on.

**Specificity control already clean:** `UNRELATED_TARGET` (a different harmful concept
remapped onto the same codeword) reads-as-concept 0.00 on every readout — the effect is
not "any harmful demonstration context".

**S3 (jobs 693558/693559) — COMPLETE.** 160 rows per readout, 4 components × 4 positions
× 32 layers, **256 cells, 0 missing**.

**S4 — COMPLETE, and it answers the plan's §2 question directly.**

- `cos(d_Direct, d_DS)` at `resid_post` / codeword position is **low**: mean 0.279
  (`cloze`) and 0.193 (`one_word`), range 0.10–0.49. **The two causal directions are not
  equivalent** — independent confirmation, at the representation level, of the behavioral
  sufficiency dissociation the prior sprint found. §2's instruction not to assume
  `d_Direct ≡ d_DS` was correct.
- The divergence is **position-specific**: at the *final prompt* token the same cosine is
  0.83. So Direct and DS look alike where the request is summarised, and differ precisely
  **at the codeword** — which is where the hijack lives.
- **Cross-fit stability is high:** `cos(d_DS^dev, d_DS^heldout)` = 0.93–0.97 across layers,
  on **text-disjoint** demonstration pools. The DS direction is a property of the pair,
  not of the particular demonstration sentences.
- **Static embeddings are untouched:** `d_DS` is *exactly zero* at `resid_pre` layer 0,
  because DOUBLESPEAK and NEUTRAL contain the same codeword token. The hijack is purely
  contextual, never lexical — the plan's §2 embedding/contextual-state distinction,
  confirmed automatically by the pipeline. (This is why the cosine is NaN there; the
  reporting is now nan-safe and records the degenerate layers explicitly.)

**Third existing-code bug found (and fixed).** `10_layerwise_knockout.py:113` used
`demo_keys = range(0, first_idx[-1])` — the *pre-F2* boundary, which blocks the
instruction prefix and the substituted query as well as the demonstrations. The F2 fix
had been applied to `09_attention_knockout.py` only, so the per-layer knockout result was
computed with a confounded "demos" set. The boundary logic now lives in one place
(`ds_common.request_start_token`, which also reports whether it actually located the
prefix rather than silently falling back) and both scripts call it. **The affected
per-layer knockout claim must be re-run before it is cited again** — logged under S8.

### ITER3 — 2026-07-29 — the full S2 run forced a methodological correction (and it mattered)

The n=80 smoke had shown a perfect gate. The **full 800-prompt run did not**, and the
reason turned out to be important rather than a nuisance:

**The positive control is not uniform across demonstration styles.** With `dialogue`-style
demonstrations, `DIRECT_CONCEPT` — where the concept word appears *literally* in the demos
— is frequently *not* read as the concept (0.00 for `cloze`, 0.17 for `repeat_concept`).
In such a cell a low `DOUBLESPEAK` score is **uninterpretable**: "no hijack" and "the
readout does not work here" are indistinguishable.

Per plan §16.4 the rule is *fix the readout, do not reinterpret the intervention*. So the
gate is now evaluated **per (readout × demo-style) cell**, and causal analysis is
restricted to cells where both controls pass. Excluded cells are listed explicitly in the
summary rather than being silently averaged in.

**This is not cosmetic — it changes the headline by ~60%:**

| | all cells | gate-passing cells |
|---|---|---|
| `DOUBLESPEAK` reads-as-concept | 0.313 (n=150) | **0.500** (n=84) |

and on the gate-passing cells the paired contrast is
`DS − Neutral` reads-as-concept **+0.500 [+0.393, +0.607]** and
`p_concept` **+0.307 [+0.249, +0.367]** (n=84, CI reliable).

Averaging over cells where the readout is *demonstrably broken* understated the hijack by
about 40%. Any study that fixes one demonstration style and one readout template would
have landed somewhere in that range essentially by luck — which is a methodological point
worth making in the paper.

Per-style structure (`cloze`, DOUBLESPEAK reads-as-concept): technical 1.00, news 0.83,
narrative 0.50, academic 0.00, dialogue 0.00 — but the last two are *excluded*, because
their positive controls fail. The hijack is strongest exactly where the readout is
demonstrably sound.

**Specificity holds at full n:** `UNRELATED_TARGET` 0.00–0.03 and `BENIGN_REMAP` 0.00
reads-as-concept across every readout — the effect is not "any remapping" or "any harmful
demonstration context".

`31_validate_readouts.py` gained a `--reanalyze` mode so a methodological correction like
this one costs no GPU time.

---

## Next single highest-value experiment

S5 layer scan (jobs 693570/693571) → then S6. The layer scan says *where* adding `d_DS` vs `d_Direct` moves
the interpretation; S6 then runs the ≥20-draw control battery and the signed-α dose response at those
layers, which is what converts "the direction correlates with meaning" into "the direction *causes*
meaning, reversibly, beyond any matched perturbation". Also queued behind it: re-running the per-layer
attention knockout with the corrected demo boundary (S8).
