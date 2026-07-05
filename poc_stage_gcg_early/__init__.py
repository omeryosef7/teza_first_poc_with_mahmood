"""
Stage GCG-Early: GCG optimizer with representation-alignment objectives.

Scientific question: Can a discrete optimized suffix make the first X generated-token
hidden states resemble those of a matched unsuccessful control while preserving later
target-task success?

Optimizer: Greedy Coordinate Gradient (Zou et al., 2023; arXiv:2307.15043).
New contribution: differentiable representation-distance and early-logit-KL objectives.

Package layout:
  config.py                   — typed dataclass configuration
  model_adapter.py            — Qwen3/Gemma4 embedding access, EOS, template
  suffix_token_manager.py     — suffix span computation via subsequence search
  selected_state_capture.py   — hook-based hidden state capture (wraps Stage AE)
  reference_cache.py          — deterministic cache of reference activations
  objectives.py               — task_loss, repr_loss, kl_loss, regularization_loss
  gcg_optimizer.py            — main GCG loop with full resume support
  build_safe_surrogate_manifest.py — harmless surrogate dataset
  run_optimization.py         — CLI entry point
  evaluate_optimized_suffixes.py   — free-generation evaluation
  analyze_pareto_frontier.py  — Pareto analysis
  analyze_detection_delay.py  — detection delay analysis
  audit_run.py                — run completeness audit
  tests/                      — unit tests (CPU-only unless marked gpu_integration)
"""
