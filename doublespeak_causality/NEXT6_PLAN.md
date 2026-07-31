# NEXT6 — "All new directions" sprint plan

## Context
NEXT5 delivered two wins (W1 per-pair TOCTOU; W3-b superposition), a validated per-head z-AtP
circuit (mid-band L7–14, distributed), and honest bounds/negatives (W2 DeepSeek weak; W5 additive
defense unstable). NEXT6 pushes every open direction to depth, per the user's request. Standing
constraints unchanged: no SLURM deps; ≤6 parallel L40S jobs (n-801..805,t-806; env poc_stage2);
job-isolate captures; reuse code; gate every claim (positive controls, true-patch validation,
paired bootstrap + a single Holm family); report negatives honestly; **cyber-safeguard — subagents
scalar-only, never open bench prompt text or raw completions, never reproduce harmful text**.
Docs: `NEXT6_FINDINGS.md`; commit+push per landed direction.

## Directions
- **D1 — W1 tier-2 (per-pair Holm-robustness).** Rerun the TOCTOU factorial at n=60 (bench has 60
  unique pids) for grenade+chlorine, re-reduce with `INTERACTION_mid_late`; test whether each pair
  individually becomes Holm-robust at its own MID depth (NEXT5 pooled it; per-pair was underpowered
  at n=40). GPU ×2. Reuse `45_toctou_factorial.py`, `ds_stage4_toctou.slurm` (N_ITEMS=60, SKIP_REFUSAL=1).
- **D2 — Superposition generalization.** Run `next5_w3b_superposition.py` on grenade/chlorine/pistol
  (Llama) and on Qwen3 (bomb) — does the DS rep carry codeword+concept across pairs AND
  architectures? CPU where reps+directions exist; GPU extraction (`32`/`33`) only if missing.
- **D3 — Circuit generalization.** z-AtP head map (`49_head_attribution.py`) on grenade+chlorine
  (LAUNCHED 697370/697371), plus Qwen3 (bomb) and possibly Phi-4 — does the mid-band (L7–14) circuit
  replicate across pairs/architectures? GPU.
- **D4 — Path patching (deepest).** Extend the z-hook to full sender→receiver path patching (freeze
  all non-sender heads at clean, patch only the sender-head→receiver edge) to test whether the
  mid-band heads form a directed circuit, not just parallel contributors. New code on `ZHeadPatch`
  + a frozen-clean forward; validate against the composed effect. GPU.
- **D5 — Phi-4 3rd architecture.** `microsoft/Phi-4-mini-reasoning` (cached) is a genuinely distinct
  (non-Llama) reasoning architecture. Readout gate (`31 --answer-marker`), and if it passes, the S2
  transplant chain — a cleaner 3rd architecture than DeepSeek (Llama-distilled). GPU.
- **D6 — Unified depth story (CPU).** Synthesize the three depth signals into one narrative: where
  the concept superposition-component EMERGES across layers (W3-b per-layer), where attention heads
  WRITE it (z-AtP by-layer, peak L9), and where the refusal check acts (T3 pair-dependent depth) —
  do they line up into a coherent install→check→carry timeline? Reuses NEXT5 artifacts. Zero GPU.
- **D7 — Defense redo (W5).** Two fixes to the NEXT5 negative: (a) small-α regime (α∈{2,3,4,6}) to
  avoid the generation-degeneration seen at α≥8; (b) evaluate the defense against attack WITH
  headroom — the TOCTOU-produced malicious behavior (concept installed + refusal ablated ≈0.53
  malicious), testing whether re-adding refusal at the use-depth suppresses it. GPU.

## Execution & orchestration
Quick/confident jobs launched first (D3). A workflow maps every reps/directions dir → (pair, model,
split) and designs D1/D2/D4/D5/D7 run-specs in parallel (scalar/summary/code/doc only). D6 runs CPU
in the main loop now. New code (D4 path-patch, D7 defense, D5 Phi-4 slurm) written in the main loop
(model-touching + safety-sensitive), then submitted. Reductions + findings drafted in parallel
workflows as scalar outputs land. Single Holm family across all new NEXT6 inferential claims.

## Verification
Per-direction gates (as NEXT5): true-patch validation for D3/D4; positive-control gate for D5/D2;
regression checks for D1; equivalence margins for any null; one Holm family; artifact-vs-doc
consistency; extend the test suite for the D4 path-patch primitive. Honest negatives are first-class.
