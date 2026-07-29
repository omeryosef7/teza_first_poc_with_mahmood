# Causal Core — Progress Tracker

**Live status doc for [`CAUSAL_CORE_PLAN.md`](CAUSAL_CORE_PLAN.md).** This is the single place to see what
has been executed, what is running, and what the numbers are. Updated every iteration (loop cadence 30 min).

States: `NOT_RUN` · `RUNNING` · `PARTIAL` · `BLOCKED` · `FAILED` · `COMPLETE`

Branch: `behavioral-causality-sprint` · Started: 2026-07-29

---

## Status board

| ID | Stage (plan ref) | Status | Evidence / notes |
|----|------------------|--------|------------------|
| S0 | Audit & freeze prior results; fix overclaims (§16.1–2) | ✅ `COMPLETE` | [`RESULTS_FREEZE_AUDIT.md`](RESULTS_FREEZE_AUDIT.md) — ~85% of ~100 claims VERIFIED; 12 wording corrections applied to `PAPER_DRAFT.md` (incl. title), 2 unsupported claims withdrawn/flagged |
| S1 | Phase A: fixed-pair CARROT↔BOMB semantic benchmark (§3, §16.3) | ✅ `COMPLETE` | `data/pair_benchmark/pair_carrot_bomb.json` — 800 semantic + 900 behavioral prompts, 60 paraphrases, **0 skipped**, 21/21 tests pass |
| S2 | Readout validation: Direct+ / Neutral− controls (§16.4) | ✅ **COMPLETE — GATE PASSED per-cell** | full run 693557 (800 prompts). **17/30 (readout × demo-style) cells usable.** On usable cells: `DS − Neutral` reads-as-concept **+0.500 [+0.393, +0.607]**, p_concept **+0.307 [+0.249, +0.367]**, n=84. |
| S3 | Rep extraction: layers × positions × components (§16.5) | ✅ `COMPLETE` ×2 | jobs 693558 (`cloze`) / 693559 (`one_word`); 160 rows each, **256 cells, 0 missing position cells**, 4 components × 4 positions × 32 layers |
| S4 | Cross-fitted `d_Direct` / `d_DS` + subspaces (§2, §16.6) | ✅ `COMPLETE` ×2 | 160 directions + 64 PCA subspaces per readout |
| S5 | Intervention sweeps add/remove/replace (§4, §16.7) | ✅ `COMPLETE` | jobs 693570 (`cloze`) / 693571 (`one_word`), `--mode layer_scan`, α∈{1,2}, all 32 layers, cross-fitted |
| S6 | Dose-response + ≥20 matched controls (§4.5, §5, §16.8) | ✅ `COMPLETE` — ⭐ | 693609: `add_d_Direct` at codeword sites **+0.533 mid / +0.971 late**, Holm-significant, **exceeds all 180 matched controls**; `add_d_DS` and 3 other remap directions **exactly 0** at matched relative strength. Signed dose 693607/693608 COMPLETE: `d_Direct` controls the reading **bidirectionally** (add→install, project-out→reduce), monotone in α (Spearman +0.81/+0.86); `d_DS` inert in both directions on **both** readouts. |
| S7 | Held-out paraphrase confirmation (§14, §16.9) | `NOT_RUN` | cross-fitting is ON by default in `34`; Holm correction wired in `35` |
| S8 | Attention knockout + attn-vs-MLP patching (§6, §16.10) | ✅ `COMPLETE` — **negative** | knockout at both granularities is **NOT demonstration-specific**: all-layers `demos_all` −99.9% vs count-matched `random_matched` −99.7% (693647); per-layer −0.0057 vs −0.0077 (693623). Component patching ≤0.019 (693614). Bears on the prior sprint's P6/RQ4 routing claim. |
| S9 | Causal attack-window estimate (§16.11) | `PARTIAL` | `add_d_Direct` peaks at **late** (0.97) not mid; `projout_d_Direct` removal peaks at **mid** (−0.16). Install and remove windows differ — needs writing up as a result, not a single number. |
| S10 | Causal objective terms, each intervention-validated (§7, §16.12) | `NOT_RUN` | |
| S11 | Continuous soft-prompt positive control (§8.5, §16.13) | ✅ `COMPLETE` — **gate RESOLVED** | Took 4 attempts, 3 of them artefacts (vacuous `free` params → frozen optimizer → missing discretization). Final (693655/6/7): relaxed ~1.0 but **discretized ≈0.006** for the concept (~0.6% retention). NOT unreachability — the real DS demo block hits **0.476** at the same positions, so this is an **optimization gap**. |
| S12 | Demonstration-level GCG/MAC — gated on S11 (§8.6, §16.14) | `UNBLOCKED` — not yet started | gate resolved: the target IS token-achievable (existence proof), gradient relaxation just fails to find it. Must init from / benchmark against the real DS demo block, success = **held-out behavioral ASR** (§9), not the causal score. |
| S13 | Codeword properties incl. embedding distance (§8.1, §16.15) | `NOT_RUN` | |
| S14 | Qwen3 thinking on the fixed pair (§G, §16.16) | `NOT_RUN` | |
| S15 | DeepSeek tokenizer localization + regression tests (§16.17) | `PARTIAL` — correctness fixed, coverage 80% | failures 192/480 → 96/480; `codeword_last` correctness on DeepSeek **28.8% → 100%**; other 3 models bit-identical; 43/43 tests |
| S16 | Scale ≥10 pairs + replication — gated (§F, §16.18) | `NOT_RUN` | |
| S17 | Documentation / registry / job tables (§15, §16.19) | `RUNNING` | this file + `RESULTS_FREEZE_AUDIT.md`; registry/checksum manifest still owed (audit finding) |

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
| 693570 | S5 layer_scan `cloze` | `run_pair_interv.sh` | t-806 | 2026-07-29 | ✅ COMPLETE (15 390 rows) | `outputs/pair_interv_layer_scan_*_693570` |
| 693571 | S5 layer_scan `one_word` | `run_pair_interv.sh` | n-803 | 2026-07-29 | ✅ COMPLETE (15 390 rows) — null after Holm | `outputs/pair_interv_layer_scan_*_693571` |
| 693595/6 | S6 dose | `run_pair_interv.sh` | n-803 | 2026-07-29 | 🔴 FAILED — argparse read `-1.0,...` as a flag | — |
| 693597 | S5 replace `cloze` | `run_pair_interv.sh` | — | 2026-07-29 | ✅ COMPLETE (2 760 rows) — **clean negative** | `outputs/pair_interv_replace_*_693597` |
| 693607 | S6 dose `cloze` | `run_pair_interv.sh` | t-806 | 2026-07-29 | ✅ COMPLETE (38 688 rows) | `outputs/pair_interv_dose_*_693607` |
| 693608 | S6 dose `one_word` | `run_pair_interv.sh` | n-802 | 2026-07-29 | ✅ COMPLETE (38 688 rows) — replicates `cloze` | `outputs/pair_interv_dose_*_693608` |
| 693609 | S6 controls `cloze` | `run_pair_interv.sh` | n-803 | 2026-07-29 | ✅ COMPLETE (11 760 rows) — ⭐ **main causal result** | `outputs/pair_interv_controls_*_693609` |
| 693613 | S8 knockout | `run_pair_attn.sh` | n-804 | 2026-07-29 | ⚠️ SUPERSEDED — demo/request boundary unlocated on 216 rows | `outputs/pair_attn_knockout_*_693613` |
| 693614 | S8 component | `run_pair_attn.sh` | n-804 | 2026-07-29 | ✅ COMPLETE (1 552 rows) | `outputs/pair_attn_component_*_693614` |
| 693618 | S8 knockout ("boundary fixed") | — | 2026-07-29 | ⚠️ SUPERSEDED — the fix did NOT work: boundary unlocated on **6912/6948** rows | `outputs/pair_attn_knockout_*_693618` |
| 693623 | S8 knockout `per_layer` (boundary verified) | `run_pair_attn.sh` | n-802 | 2026-07-29 | ✅ COMPLETE (5 796 rows, **0% unlocated**) — negative, beaten by random control | `outputs/pair_attn_knockout_*_693623` |
| 693631 | S11 soft-prompt **free** concept/demos | `run_pair_softprompt.sh` | — | 2026-07-29 | ⚠️ VACUOUS — unconstrained params reach any target | `outputs/pair_softprompt_concept_demos_*` |
| 693632 | S11 soft-prompt **free** unrelated/demos (ctrl) | `run_pair_softprompt.sh` | — | 2026-07-29 | ⚠️ VACUOUS — unconstrained params reach any target | `outputs/pair_softprompt_unrelated_demos_*` |
| 693633 | S11 soft-prompt **free** concept/readout (ctrl) | `run_pair_softprompt.sh` | — | 2026-07-29 | ⚠️ VACUOUS — unconstrained params reach any target | `outputs/pair_softprompt_concept_readout_*` |
| 693647 | S8 knockout `all_layers` | `run_pair_attn.sh` | — | 2026-07-29 | ✅ COMPLETE (216 rows, 0% unlocated) — **non-specific** | `outputs/pair_attn_knockout_*_693647` |
| 693648 | S11 soft-prompt simplex concept (lr=0.01) | `run_pair_softprompt.sh` | n-802 | 2026-07-29 | ⚠️ INVALID — optimizer frozen (`lr×steps=3` vs init gap 20) | `outputs/pair_softprompt_simplex_concept_demos_*_693648` |
| 693652 | S11 simplex concept (lr=1.0, pre-discretize) | `run_pair_softprompt.sh` | n-802 | 2026-07-29 | ⚠️ CANCELLED — superseded by 693655 | `outputs/pair_softprompt_simplex_concept_demos_*_693652` |
| 693653 | S11 simplex unrelated (pre-discretize) | `run_pair_softprompt.sh` | n-802 | 2026-07-29 | ⚠️ CANCELLED — superseded by 693656 | — |
| 693654 | S11 simplex codeword (pre-discretize) | `run_pair_softprompt.sh` | n-802 | 2026-07-29 | ⚠️ CANCELLED — superseded by 693657 | — |
| 693655 | S11 simplex **concept + discretize** | `run_pair_softprompt.sh` | n-801 | 2026-07-29 | ✅ COMPLETE — relaxed ~0.99 → **discretized ≈0.006** | `outputs/pair_softprompt_simplex_concept_demos_*_693655` |
| 693656 | S11 simplex unrelated + discretize | `run_pair_softprompt.sh` | n-802 | 2026-07-29 | ✅ COMPLETE — 0.9994 → **0.0124** | `outputs/pair_softprompt_simplex_unrelated_demos_*_693656` |
| 693657 | S11 simplex codeword + discretize | `run_pair_softprompt.sh` | n-802 | 2026-07-29 | ✅ COMPLETE — 1.0000 → **0.1016** | `outputs/pair_softprompt_simplex_codeword_demos_*_693657` |
| 693649 | S11 soft-prompt simplex unrelated (lr=0.01) | `run_pair_softprompt.sh` | n-802 | 2026-07-29 | ⚠️ INVALID — same frozen optimizer | `outputs/pair_softprompt_simplex_unrelated_demos_*_693649` |

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

### ITER4 — 2026-07-29 — S5 first scan is a NEGATIVE, and the reason is methodological

The first layer scan (job 693571, `one_word`, 15 390 rows) found **no significant additive
effect after Holm correction**: peak `add_d_Direct` = +0.028 at L3, `add_d_DS` = 0.000.

Reporting this honestly matters, and so does diagnosing it before believing it. Two causes,
both about *how the intervention was applied* rather than about the mechanism:

1. **The intervention was a one-layer, one-token edit.** The prior sprint's sufficiency
   effects (mid-window `suff_Direct` = 0.52) needed **multi-layer windows** — ten-plus
   layers patched simultaneously. Only the `replace` arm supported windows; the additive
   and projection arms did not. Fixed: `--layer-groups {single,windows,both}`.
2. **α was absolute.** The residual norm grows several-fold from L0 to L31, so a fixed α is
   a *shrinking relative* perturbation with depth and layers are not comparable. Fixed:
   `--alpha-mode relative`, where α is a fraction of the residual norm at that layer, taken
   from the `NEUTRAL_CODEWORD` mean already stored in `means.npz` (no extra forward pass).

Also, the intervention site is now `codeword_all` rather than only the final occurrence —
the codeword appears throughout the demonstrations, and the prior code intervened on one
token of it.

**A reporting bug the scan exposed.** With only 2 random draws the control distribution had
zero spread, so `z = eff/(sd+1e-9)` printed values around **1e7** — which look decisive and
mean nothing. `z` is now emitted only when the control distribution has real spread *and*
≥8 draws, and "exceeds all controls" is surfaced only when the effect is also materially
non-zero (|eff| ≥ 0.01). Beating a control set that is identically 0.0 by +0.0001 is
arithmetic, not a causal result. Had this gone unnoticed it would have produced a table of
spectacular-looking z-scores backing a null.

Re-run submitted: 693595/693596 (`--mode dose`, windows + single, relative α ∈
{−1, −0.5, +0.5, +1, +2}, site `codeword_all`) and 693597 (`--mode replace`).

### ITER5 — 2026-07-29 — S0 freeze done; the replacement arm is a clean NEGATIVE

**S0 (audit & freeze) — COMPLETE.** A four-way independent audit of `PAPER_DRAFT.md`,
`SPRINT_REPORT.md`, the results docs and the artefact inventory is written up in
[`RESULTS_FREEZE_AUDIT.md`](RESULTS_FREEZE_AUDIT.md). Roughly **85% of ~100 claims
VERIFIED**, and every headline interval reproduced exactly from raw artefacts. What did
not hold up, and what was done about it:

| finding | action |
|---|---|
| The central causal story is an **inference, not a demonstrated chain** — the timing experiment injects the *raw* concept at varying depth and never manipulates the emergence depth of the *hijacked* representation | Paper **title, abstract, §1 hypothesis box, §4.3 and §5 rewritten** to state this explicitly; added as an explicit Limitation. This is precisely the gap the fixed-pair study exists to close. |
| "falls below its random control" (sufficiency, late) — **no random arm was ever run** in any sufficiency job | claim withdrawn in `BEHAVIORAL_CAUSALITY_RESULTS.md` |
| the "126×/8181× random control" ratio is **not reproducible** and points the opposite way | flagged DO-NOT-CITE in all four docs that carry it, pointing at the artefact-backed `necessity − random = +0.181 [−0.021, 0.383]` instead |
| early-window malicious rate 0.10 vs **0.123** on disk | corrected |
| "late … compliance instead" / "never refused (0%)" | corrected — late malicious is **0.09**, *below* early and one fifth of mid; 89% of late generations are benign, so the low late refusal rate partly reflects loss of behavioral effect |
| Qwen3 **early** DS−Direct was omitted everywhere — and on disk it runs the *other way*, **+0.190 [+0.071, +0.310]** | added; the dissociation is now described as mid-specific, not uniform |
| "42 clean successes" quoted with no base rate; "66 malicious" for DeepSeek counts ineligible bases | both given denominators (42/240 across 18 bases; DeepSeek 37 on eligible bases) |
| "monotone … significant across three architectures" — only Llama has three windows | corrected to "monotone on Llama; early-vs-late reproduced on two further architectures, windows scaled per model" |
| "predictive" AUC 0.668 ± 0.089 presented beside causal results (±0.089 is a fold sd; a 2-sd band reaches chance) | relabelled modest and **correlational** |
| "cannot be optimized" / "not suffix-optimizable" | bounded: one optimizer, one model, 16 tokens, 200 steps, one placement |
| **Provenance**: `outputs/` and `data/behavioral_benchmark/` are gitignored; the registry has 39 rows all ≤ 2026-07-27 and names only 14 of ~83 output dirs | header note corrected; registry/manifest work tracked under S17 |

Note the audit also warned that the output tree was **live during the audit** (83→100 dirs)
because this sprint was writing into it. The new work uses distinct `pair_*` prefixes, so
the freeze set and the new set do not overlap.

**S5 replacement arm (job 693597, 2 760 rows) — a clean NEGATIVE, with the control the
prior sprint never had.** Transplanting the source condition's `resid_post` into the
codeword position, single layers and windows:

| arm | group | effect vs identity | shuffled-source control |
|---|---|---|---|
| `DS_from_Neutral` | mid | +0.0317 [−0.010, +0.088] | **+0.0306** |
| `DS_from_Neutral` | layer14 | +0.0308 [−0.006, +0.081] | **+0.0213** |
| `Neutral_from_Direct` | layer2 | +0.0271 [+0.018, +0.038] | **+0.0301** (larger!) |
| `Neutral_from_Direct` | layer6 | +0.0086 [+0.003, +0.015] | **+0.0138** (larger) |

**Every arm is matched or beaten by its own shuffled-source control**, and every effect is
≤ 0.03 against a DS−Neutral gap of +0.307. So single-position activation replacement shows
**no content-specific causal transfer of the meaning**: what little it does is explained by
transplanting *some* representation from that condition, not *this* prompt's.

This matters twice over. It independently reproduces the prior sprint's "the hijacked state
is only weakly sufficient when transplanted" — and it supplies the shuffled control whose
absence the audit flagged as `SOURCE_MISSING`. The prior claim was directionally right for a
reason nobody had tested.

The additive route is not yet decided: those runs (693607/693608/693609) intervene at **all**
codeword occurrences with α as a fraction of the residual norm, which is a much stronger
manipulation than one token at α=1.

**A third runner footgun found:** argparse reads a value beginning with `-` as a flag, so
`--alphas -1.0,...` died with "expected one argument" and jobs 693595/693596 produced nothing.
Signed α grids must be passed as `--alphas=...`. Fixed in the runner with a comment next to
the existing comma-truncation guard.

### ITER6 — 2026-07-29 — ⭐ S6 control battery: a controlled causal effect, and a sharp dissociation

Job 693609 (`--mode controls`, 11 760 rows): all codeword occurrences, α as a fraction of
the residual norm, multi-layer windows, **180 matched controls per cell** in three families.

**`d_Direct` causally installs the target interpretation. `d_DS` does not — at matched
relative strength.**

| arm | site | early | mid | late |
|---|---|---|---|---|
| `add_d_Direct` | `codeword_all` | **+0.167** [+0.105, +0.232] | **+0.533** [+0.453, +0.613] | **+0.971** [+0.955, +0.984] |
| `add_d_Direct` | `adjacent` (control) | — | +0.013 | +0.003 |
| `add_d_Direct` | `random_token` (control) | — | +0.004 | +0.003 |
| `add_d_DS` | `codeword_all` | +0.0000 | +0.0000 | +0.0000 |
| `add_d_benign` / `add_d_unrelated` / `add_d_repeated` | `codeword_all` | +0.0000 | +0.0000 | +0.0000 |

All `d_Direct` rows survive **Holm–Bonferroni** over the layer × α grid (p_adj = 0.0225) and
**exceed all 180 matched controls** (control distribution: mean +0.00002, max +0.0002, across
norm-matched / orthogonal / in-PCA-subspace families of 60 each).

So the effect is **position-specific** (codeword sites 0.533 vs adjacent token 0.013 vs random
token 0.004 — a 40–130× margin), **concept-specific** (three other remapping directions give
exactly zero), and **dose-ordered** in depth.

**I checked that the `d_DS` null is not a no-op**, because an exact 0.0000 is exactly what a
silently-skipped intervention looks like:
- both arms report `n_layers_patched` ∈ {10, 12} at 4–9 token positions — the DS arm ran;
- `d_DS` is a *large* vector, not a rounding artefact: ‖d_DS‖/‖h‖ = **0.44** at L15 and 0.29 at
  L28, against `d_Direct`'s 0.69/0.67. Under `--alpha-mode relative` both are rescaled to the
  same fraction of the residual norm before injection, so this is a matched-strength comparison;
- `d_unrelated` has a nearly identical norm ratio (0.47/0.36) and also does nothing, so the
  contrast is not about vector magnitude.

**Why this matters.** Four independent lines now say the same thing:
1. `cos(d_Direct, d_DS) = 0.28` at the codeword (ITER2) — they are different directions;
2. transplanting the DS state produces nothing content-specific (ITER5 replace arm);
3. adding `d_DS` at matched strength moves the interpretation by **zero** (this iteration);
4. the prior sprint's behavioral dissociation, Direct ≫ DS at mid.

Together: **the Doublespeak representation is not a "write the concept into this token"
direction.** Whatever the demonstrations do, it is not installing the concept in the
codeword's residual stream — which is precisely the reading that Patchscopes decoding
invites, and which the audit flagged as the paper's unproven inferential step.

**Caveats, stated up front.**
- `d_Direct ≈ h_bomb − h_carrot`, so adding it at every codeword position is close to a *soft
  substitution of the token*. The near-ceiling **+0.971 at late** layers, immediately upstream
  of the readout, is consistent with that reading. The positive result should be stated as
  "the target interpretation is causally installable at the codeword position", not as "we
  have found the hijack's mechanism". The **specificity** controls are what make it more than
  a norm perturbation.
- `p_codeword` behaves differently by depth: early injection *raises* the literal reading
  (0.008 → 0.488) while mid/late collapse it (→ 0.000/0.002). Early injection is being
  incorporated as content; late injection overwrites. That asymmetry is itself the dose signal.
- α ≥ 0 only in this cell; the signed dose response (693607/693608) is what tests reversibility.

**S15 (DeepSeek localization) — substantially fixed, and a worse bug found underneath.**
The deferral was recorded as "a model-specific tokenizer edge case" blocking a bonus timing
point. Measured against the real benchmark it was **192 of 480 prompts (40%) failing**, and the
cause is not an edge case: that tokenizer fuses the codeword's **first character into the
preceding token** — `"build a river."` → `'uild' | 'ar' | 'iver'` — so the codeword is not an
isolated token run at all.

Adding carrier-phrase-derived variants cut failures 192 → 39. But measuring *correctness*
rather than *success* showed the naive version was far worse than the failure count implied:
a carrier variant could absorb adjacent punctuation, so on DeepSeek only **28.8%** of the
"successful" localizations had `codeword_last` actually pointing at the end of the codeword —
the rest silently pointed at a comma. Requiring each derived variant to cover the word **and
nothing else** fixes that:

| model | fails / 480 | `codeword_last` correct |
|---|---|---|
| Llama-3.1-8B | 0 | **100%** |
| Qwen3-14B | 0 | **100%** |
| Phi-4-mini | 0 | **100%** |
| DeepSeek-R1-Distill-8B | 96 (20%) | **100%** (was 28.8%) |

DeepSeek now **fails loudly on 20% instead of silently mislocating 71% of the rest**, which is
the right trade. The three working models are bit-identical (same failure count, same mean
occurrence count) — the change cannot have perturbed any existing result. 4 regression tests
added; suite is **43/43**.

Also added `find_word_occurrences_in_text` (character-offset localization, exact) plus
`_offsets_are_sane`, because DeepSeek's own offset mapping is broken — it returns overlapping,
non-monotonic spans covering 39 of 138 characters — and trusting it would have mislocated
everything.

### ITER7 — 2026-07-29 — the S8 knockout boundary fix did NOT work; caught before it was believed

Job 693618 was submitted as "knockout with the demo/request boundary fixed". It was not
fixed. The per-row flag says `request_boundary_located = False` on **6912 of 6948 rows**.

The first fallback searched the **templated** string for the last `"\n\n"`. Llama-3.1's chat
template *ends* with `"\n\n"` (the assistant header), so `rfind` returned the very end of
the string, no token started after it, and the fallback silently declined — leaving the
original confounded boundary (the codeword's own first token) in place.

This is the third time in this sprint a boundary/localization fix looked right and was
wrong in a way only a per-row correctness flag exposed (the others: the DeepSeek carrier
variants pointing `codeword_last` at a comma, and `10_layerwise_knockout.py`'s pre-F2
span). The lesson is already encoded in the code — **every localization helper now returns
whether it actually succeeded, and every consumer records that per row** — and it is what
caught this one.

The corrected version locates the separator inside the **raw prompt** and maps it into the
templated string. Verified offline before submitting: **36/36 located**, demo span ends
`"...talk of the town.\n\n"` and the request span begins `"Complete the sentence with
exactly one word..."`. Rerun submitted.

**The 693618 numbers are therefore NOT interpretable and are not reported as a result.**
For the record they were uniformly ~0 (largest |effect| 0.009 against a DOUBLESPEAK baseline
of 0.474), but under a boundary where "demos" ran up to the final codeword and swallowed
part of the readout question — so a null there says nothing about demonstration routing.

### ITER8 — 2026-07-29 — ⭐ bidirectional control by `d_Direct`; `d_DS` inert on both readouts

**Dose response (693607 `cloze`, 693608 `one_word`, 38 688 rows each).** Both readouts give
the same picture, so this is not a readout artefact.

`add_d_Direct` on NEUTRAL prompts (baseline p_concept ≈ 0.000), by window and signed α:

| readout | window | α=−1.0 | α=−0.5 | α=+0.5 | α=+1.0 | α=+2.0 |
|---|---|---|---|---|---|---|
| `cloze` | early | 0.000 | 0.000 | +0.200 | +0.177 | **+0.673** |
| `cloze` | mid | 0.000 | 0.000 | +0.357 | **+0.536** | +0.328 |
| `cloze` | late | 0.000 | 0.000 | +0.654 | +0.973 | **+0.987** |
| `one_word` | late | 0.000 | 0.000 | +0.088 | +0.332 | **+0.677** |

Monotone in positive α (Spearman +0.81 `cloze`, +0.86 `one_word`). `mid` peaks at α=1 and
*falls* at α=2 (over-steering); `late` saturates near ceiling.

**Negative α is uninformative here, and the analyzer now says so rather than reporting a
failed test.** The NEUTRAL baseline is already ≈0, so there is no room to push the concept
reading *down* — every negative-α cell is identically 0.000 **by construction**. Reporting
that as `reversible: False` would read as evidence against reversibility. `35_analyze` now
emits `floor_limited_downward: true` and `reversible: null` for such cells, and downward
control is measured where the score is high instead — by projecting the direction **out of a
DOUBLESPEAK prompt**.

**Downward control works, and it is `d_Direct` again** (`projout_*` on DOUBLESPEAK,
baseline 0.215 `cloze` / 0.128 `one_word`):

| arm | window | `cloze` | `one_word` |
|---|---|---|---|
| `projout_d_Direct` | mid | **−0.157 → −0.160** | −0.059 → −0.044 |
| `projout_d_Direct` | late | −0.068 → −0.069 | −0.065 → −0.048 |
| `projout_d_Direct` | early | **+0.192** | **+0.280** |
| `projout_d_DS` | any | −0.03 … +0.04 | −0.05 … +0.01 |

So `d_Direct` controls the interpretation **bidirectionally** — adding it to a Neutral prompt
installs the reading, removing it from a Doublespeak prompt reduces it — while `d_DS` does
**neither**, on both readouts. That is now five independent lines pointing the same way.

One further result worth flagging: removing the Direct component **at early layers
increases** the final concept reading (+0.19 / +0.28). Suppressing the concept signature
early makes the meaning *more* readable later — which is the direction a time-of-check
account predicts, and it is a manipulation the prior sprint never performed.

**S8 attention knockout (693623, 5 796 rows, boundary 0% unlocated) — a NEGATIVE.**
Blocking attention from the final codeword token to the demonstrations barely moves the
reading, and is **beaten by its own count-matched random control**:

| source set | effect | baseline |
|---|---|---|
| `random_matched` (control) | **−0.0077** [−0.0114, −0.0043] | 0.474 |
| `demos_all` | −0.0057 [−0.0091, −0.0023] | 0.474 |
| `request_only` (control) | +0.0032 | 0.474 |
| `prev_codewords` | +0.0006 (NS) | 0.474 |

Individual layers do show localized effects (L2 −0.072, L10 −0.060, L14 −0.049, all CI-
excluding-0), but the aggregate is ≈ the random control. **Caveat that bounds this:** the run
used `--granularity per_layer`, so each row blocks one layer only, whereas the prior sprint's
knockout result blocked *all* layers simultaneously. The all-layers test is the correct
comparison and is running (693647). Until it lands, "demonstration routing is not required"
is **not** a claim I am making.

### ITER9 — 2026-07-29 — S8 all-layers knockout is NON-SPECIFIC; S11 gate is VACUOUS as first run

**S8 all-layers knockout (693647, 0% unlocated).** Blocking attention from the final
codeword token to the demonstrations, at *every* layer simultaneously, destroys the hijacked
reading almost completely — and so does the count-matched random control:

| source set | effect | mean after | baseline | reduction |
|---|---|---|---|---|
| `demos_all` | −0.4740 [−0.6131, −0.3296] | 0.0003 | 0.4742 | **−99.9%** |
| `random_matched` (count-matched control) | −0.4728 [−0.6117, −0.3286] | 0.0015 | 0.4742 | **−99.7%** |
| `demos_first` | −0.4391 | 0.0351 | 0.4742 | −92.6% |
| `request_only` | −0.0781 | 0.3961 | 0.4742 | −16.5% |
| `prev_codewords` | −0.0133 (NS) | 0.4609 | 0.4742 | −2.8% |

**The demonstration knockout is indistinguishable from blocking the same number of random
earlier tokens.** Removing ~154 tokens of attention at every layer simply destroys the
codeword's representation; it is a lesion, not a localization. The same held at `per_layer`
granularity (693623: `demos_all` −0.0057 vs `random_matched` −0.0077).

**This bears directly on an existing claim.** The prior sprint recorded P6/RQ4 as "blocking
codeword→demos removes the hijack (0.10→0), distributed across layers". That effect
reproduces here in magnitude — but with a count-matched random control it is **not
demonstration-specific**, so it does not support the conclusion that the mapping is *routed*
from the demonstrations. Combined with the boundary bug in `10_layerwise_knockout.py`
(ITER2), the attention-routing claim needs re-deriving before it is cited again. Logged for
`SPRINT_REPORT.md` / `PAPER_DRAFT.md`.

Note what *is* specific: `prev_codewords` (blocking only the earlier codeword occurrences,
~4 tokens) does essentially nothing (−2.8%, NS). So the hijack does not depend on the final
codeword attending to its own earlier mentions.

**S11 gate (693631/2/3) — the positive control PASSED VACUOUSLY, and the control caught it.**

| run | p_start → p_best |
|---|---|
| concept / demos (main) | 0.00000 → **0.99990** [+0.99977, +0.99997] |
| **unrelated target / demos** | 0.00094 → **0.99985** [+0.99858, +0.99921] |
| concept / readout positions | 0.00000 → 0.874 |

Unconstrained soft prompts over 58–202 positions reach *any* target essentially perfectly.
That says the optimizer works; it says **nothing** about whether the causal objective is
reachable by a demonstration attack, because a free vector in ℝ^4096 per position has far
more capacity than any token. Without the `unrelated` control this would have read as
"the objective is optimizable — proceed to GCG", and the S12 result would have been built on
sand.

Fix: `--param simplex` parameterises each free position as **logits over the vocabulary**,
using the softmax-weighted convex combination of embedding rows. Any real token sequence is
a vertex of that simplex, so its optimum is a genuine upper bound for a discrete attack.
Initialised at the actual tokens (step 0 reproduces the real prompt), and the run now reports
`mean_peak_weight` — how close the relaxed solution is to a one-hot token sequence — so a
"success" spread across the vocabulary can be told apart from an achievable one. Rerun as
693648 (concept) / 693649 (unrelated control), 300 steps.

**The S11 gate is therefore still OPEN**, and S12 (discrete GCG/MAC) remains blocked, which
is the correct state per §8.5.

### ITER10 — 2026-07-29 — the simplex "null" was an optimizer artefact; caught by arithmetic

The vocabulary-simplex rerun (693648/693649) reported, for the concept target,
`p_start = 0.00000 → p_best = 0.00000` on **every** prompt. Read naively that is a headline:
*the causal objective is not reachable through the demonstration tokens at all.*

It is not a result. The simplex logits are initialised at ±`init_scale` = ±10 so that step 0
reproduces the real prompt, which puts a gap of **20 logit units** between the initial token
and every alternative. Adam moves a logit by roughly `lr` per step, so the run's budget was
`lr × steps = 0.01 × 300 ≈ 3` — **the argmax could not change even in principle.** The
observed `mean_peak_weight` drifting only from 0.9997 to ~0.92 is the fingerprint of exactly
that: the distribution wobbled and never switched a single token.

The unrelated-target control shows the same fingerprint from the other side — it moved
0.0005 → 0.0094 (≈18×, but still ~0.01 absolute), i.e. the optimizer nudged the distribution
without ever leaving the initial token sequence.

**Fixes, so this class of failure reports itself rather than masquerading as a finding:**
- `--lr` default raised to **1.0** for `simplex` (it acts on vocabulary *logits*, not on
  embeddings — an O(0.01) rate is appropriate only for `--param free`);
- every run now emits `frac_positions_changed` (how many positions' argmax actually moved),
  `optimizer_moved`, `logit_budget = lr × steps`, `init_gap = 2 × init_scale` and
  `budget_sufficient = logit_budget > init_gap`. A null with `optimizer_moved: false` is
  self-evidently uninterpretable.

Rerun: 693652 (concept), 693653 (unrelated control), 693654 (**codeword** — a reachability
reference: the literal reading is what the prompt already supports, so if the optimizer
cannot even raise *that*, the harness is broken rather than the objective unreachable).

This is the fourth time this sprint a null or a success turned out to be an artefact of the
mechanism rather than the phenomenon (the others: the pre-F2 knockout span, the DeepSeek
carrier variants, the unconstrained soft prompt). The pattern is consistent enough to state
as a working rule for this codebase: **never accept a null without a positive control that
proves the intervention could have moved the outcome.**

### ITER11 — 2026-07-29 — S11 gate RESOLVED: an optimization gap, not an unreachability result

With `lr=1.0` the simplex optimizer finally moves (19–41% of positions change argmax), and
the **discretization check** — added precisely because `peak_w ≈ 0.80` meant the relaxed
optimum is a *blend* no real prompt can be — settles the gate.

| target | start | relaxed `p_best` | **discretized** | retention |
|---|---|---|---|---|
| **concept** (bomb) | 0.0000 | ~0.99 | **≈0.006** (per-prompt 5e-05, 0.034, 0.0, 1e-06, 1e-06, 1.2e-05) | **~0.6%** |
| codeword (carrot) | 0.0044 | 1.0000 | 0.1016 | 10.2% |
| unrelated (virus) | 0.0009 | 0.9994 | 0.0124 | 1.2% |

**~99% of the relaxed "success" evaporates on discretization.** Had the relaxed number been
reported as the gate result — which both earlier attempts would have done — S12 would have
launched believing the objective fully reachable.

**But the natural reading of that table is wrong, and the data says so.** "Discretized ≈ 0,
therefore the causal objective is not reachable through demonstration tokens" is refuted by
an existence proof already in hand: the **real Doublespeak demonstration block is a token
sequence at exactly those positions**, and it achieves

| prompt at the demo positions | p_concept (cloze, gate-passing styles) |
|---|---|
| `NEUTRAL_CODEWORD` demos (the soft-prompt starting point) | **0.0000** |
| `DOUBLESPEAK` demos (real tokens, same slots) | **0.4756** |

So a token sequence achieving a high causal score demonstrably exists. The soft-prompt
relaxation simply fails to find it. **The S11 gate therefore reports an OPTIMIZATION gap,
not unreachability** — and that distinction decides what happens next.

**Consequences.**
1. **Continuous relaxation provides no useful upper bound here.** Its optimum lives
   off-manifold (mean peak weight 0.79–0.99, but the *minimum* per-position weight is what
   matters — job 693655 prompt 1 had mean peak 0.991 yet discretized to 5e-05, i.e. a
   handful of blended slots carried the entire effect). `min_peak_weight` and
   `n_blended_positions` are now reported so this is visible without discretizing.
2. **S12 is unblocked, but on a corrected rationale.** Per §8.5 the gate exists to stop us
   interpreting a discrete failure as impossibility. We now know the target is achievable by
   tokens, so a discrete search failing would be informative about the *search*, and a
   discrete search succeeding is meaningful. S12 should be initialized from / benchmarked
   against the real DS demo block (p_concept 0.476) rather than from Neutral, and its
   success criterion must be **held-out behavioral ASR** (§9), not the causal score.
3. **This also reframes the prior sprint's suffix-GCG negative.** That result was reported as
   "the mechanism is not distillable into a suffix". The present evidence suggests a simpler
   explanation is available — gradient-relaxation methods are simply poor at this objective,
   independent of whether the mechanism is distillable — so the negative should stay bounded
   exactly as `PAPER_DRAFT.md` now words it.

A caution on the earlier `unrelated`-target control, recorded so the mis-specification does
not propagate: for the *unconstrained* parameterization it correctly exposed a vacuous pass.
Under the simplex it is the wrong control, because teaching a codeword an arbitrary meaning
through demonstrations **is the Doublespeak premise**, not a confound. The controls that
discriminate here are discretization retention, transfer to held-out readouts, and behavioral
ASR.

---

## Next single highest-value experiment

**S10 (define the causal objective), then S12.** The S11 gate is resolved.

Superseded text: Everything else in the chain has landed; the objective work
is what the plan actually builds toward, and it cannot start until the §8.5 gate returns an *informative*
answer. Two outcomes are both publishable: if the vocabulary-simplex relaxation can drive the causal score
while the unrelated-target control cannot, the objective is genuinely optimizable at demonstration positions
and S12 proceeds; if it cannot, then the causal quantity that `d_Direct` controls so cleanly at the
representation level is **not reachable through the demonstration tokens at all**, which would explain the
prior sprint's suffix-GCG negative without appealing to optimizer weakness.

Superseded plan text (kept for the record):
Two things are worth more than anything else right now:

1. **The signed dose response (693607/693608)** — reversibility is the remaining piece of §4.5. If negative α
   pushes the interpretation *away* from the concept, `J_causal = P(target | do(+d)) − P(target | do(−d))`
   becomes a well-defined objective (§7) and S10 can proceed.
2. **Explaining the `d_DS` null.** It is the most informative number in the sprint: the direction that
   *characterises* a hijacked prompt cannot *cause* the hijacked reading. The natural next test is whether
   the DS mapping is carried by attention **from the demonstrations** rather than by the codeword's own
   residual content — which is exactly what S8's knockout (693618) measures. If knocking out
   codeword→demonstration attention destroys the reading while `d_DS` addition cannot install it, the
   mechanism is *routing*, not *content*, and that is a genuinely new claim about Doublespeak.
