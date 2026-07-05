"""poc_stage_ae — Paired A/E(+D/G) early-token expansion pipeline.

Stages:
  1. build_ae_manifest.py       — manifest construction (Qwen3 + Gemma4, conditions A/D/E/G)
  2. run_ae_generation.py       — generation runner (one process per model x goal_index x condition)
  3. thinking_position_utils.py — shared marker/position location module
  4. replay_hidden_states.py    — deterministic hidden-state replay via forward pre-hooks
  5. score_ae_outputs.py        — StrongREJECT scoring + heuristic failure taxonomy
  6. audit_ae_run.py            — completion audit / resume-target computation

See docs/STAGE_AE_EARLY_TOKEN_PROGRESS.md for live execution status and
docs/SLURM_AND_MODEL_AUDIT.md / docs/IMPLEMENTATION_AUDIT.md for design rationale.
"""
