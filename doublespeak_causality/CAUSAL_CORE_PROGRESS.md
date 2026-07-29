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
| S2 | Readout validation: Direct+ / Neutral− controls (§16.4) | `RUNNING` | job 693555 (smoke, `DSLIMIT=80`) |
| S3 | Rep extraction: layers × positions × components (§16.5) | `NOT_RUN` | code ready: `32_extract_pair_reps.py` + `pair_common.py` |
| S4 | Cross-fitted `d_Direct` / `d_DS` + subspaces (§2, §16.6) | `NOT_RUN` | code ready: `33_build_directions.py` (CPU) |
| S5 | Intervention sweeps add/remove/replace (§4, §16.7) | `NOT_RUN` | code ready: `34_intervention_sweep.py --mode layer_scan` |
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
| 693555 | S2 smoke | `run_pair_readout.sh` `DSLIMIT=80` | n-803 | 2026-07-29 | RUNNING | `outputs/pair_readout_Llama-3.1-8B-Instruct_*` |

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

---

## Next single highest-value experiment

S2 — the readout gate (job 693555). Nothing downstream is interpretable until at least one safe semantic
readout separates `DIRECT_CONCEPT` from `NEUTRAL_CODEWORD`. Immediately after it passes: S3 rep extraction
on the full benchmark, then S4 (CPU) and the S5 layer scan.
