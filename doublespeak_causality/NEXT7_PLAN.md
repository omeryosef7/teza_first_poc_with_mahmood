# NEXT7 — continuous divergence sprint (autonomous /loop)

## Context
NEXT6 established: the Doublespeak context effect is a **distributed, MLP-involving mid-band
computation, not a sparse attention-head circuit** (D3+W4+D4 converge); superposition is bomb-specific
but cross-architecture (Qwen3); TOCTOU generalizes to grenade (n=60, p=0.008) but not chlorine;
reasoning models (DeepSeek, Phi-4) don't carry the hijack to the answer; late-depth defense fails.
NEXT7 diverges into the NEW questions those results open. Constraints unchanged: no SLURM deps, ≤6
parallel L40S jobs, job-isolate, reuse code, gate every claim, single Holm family, cyber-safeguard
(subagents scalar-only, no bench/completion text), honest negatives. Docs: `NEXT7_FINDINGS.md`.

## Directions (each follows directly from a NEXT6 result)
- **N7-A — MLP-node attribution [follows D4].** D4 showed the effect is MLP-mediated (heads have
  DIRECT≈0). Localize WHICH MLP sublayers carry the concept-readout effect via a per-layer MLP AtP
  (capture layer.mlp output+grad; AtP vs true MLP patch via SubmodulePatch; trustworthiness gate) on
  bomb, then grenade/chlorine. New `51_mlp_attribution.py`. GPU.
- **N7-B — reasoning-model CoT probe [follows D5].** Test whether thinking models carry the hijacked
  reading EARLY in the CoT but RESOLVE it before the answer (reasoning as implicit defense). Score
  concept-vs-codeword mass at a grid of CoT positions + the answer, DS vs Neutral, on Qwen3-thinking
  and DeepSeek. New `52_cot_concept_trajectory.py`. GPU.
- **N7-C — Qwen3 mid-band circuit [follows D3].** Does the mid-band z-AtP circuit cross to Qwen3?
  Needs a thinking-aware metric position. GPU (later iteration).
- **N7-D — pair-coverage completion [follows D1].** T3 refusal-depth probe on cocaine + pistol
  (running: 698695/698696) to get their dominant depths, then behavioral TOCTOU at those depths —
  does the per-pair-timing TOCTOU generalize beyond grenade? GPU.
- **N7-E — node-level full circuit [follows D4].** Combine attention-sublayer + MLP nodes into one
  path-patch graph (the D4 fallback) once N7-A localizes the MLP nodes. GPU (later).

## Execution & orchestration
Confident runs launched first (N7-D). A workflow designs N7-A/N7-B code specs in parallel (scalar/
code/doc only). New code written in the main loop (model-touching), then real SLURM runs. Reductions
+ findings as scalar outputs land. Self-paced /loop: each wake reduces landed jobs, implements the
next designed direction, launches its run, and diverges further. Continues until the user says stop.

## Verification
Per-direction gates (true-patch validation for N7-A; positive control + neutral baseline for N7-B;
regression/equivalence as needed); one Holm family across NEXT7 positive claims; artifact-vs-doc
consistency; extend the test suite for new primitives; honest negatives first-class.
