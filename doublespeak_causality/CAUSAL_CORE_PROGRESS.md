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
| S1 | Phase A: fixed-pair CARROT↔BOMB semantic benchmark (§3, §16.3) | `NOT_RUN` | |
| S2 | Readout validation: Direct+ / Neutral− controls (§16.4) | `NOT_RUN` | |
| S3 | Rep extraction: layers × positions × components (§16.5) | `NOT_RUN` | |
| S4 | Cross-fitted `d_Direct` / `d_DS` + subspaces (§2, §16.6) | `NOT_RUN` | |
| S5 | Intervention sweeps add/remove/replace (§4, §16.7) | `NOT_RUN` | |
| S6 | Dose-response + ≥20 matched controls (§4.5, §5, §16.8) | `NOT_RUN` | |
| S7 | Held-out paraphrase confirmation (§14, §16.9) | `NOT_RUN` | |
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
| _(none yet)_ | | | | | | |

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

---

## Next single highest-value experiment

S1 — build the fixed-pair CARROT↔BOMB semantic benchmark, because every later stage (directions,
interventions, controls, objective) consumes it, and it is CPU-only so it can be built while GPU work for
S0's audit re-verification is unnecessary.
