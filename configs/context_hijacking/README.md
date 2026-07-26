# configs/context_hijacking — CPU scaffold (PROVISIONAL + PLAN)

Scaffold for Phase F2 (context-hijacking / Doublespeak). **No model is run here.**
This directory only enumerates experiment cells; all GPU execution is deferred and
needs approval per the sprint HARD RULES.

- `conditions.yaml` — enumeration of the F2.1 behavioral conditions (C1–C8), the
  targets/datasets/frozen-scorer to reuse, and the F2.2/F2.3 design + GPU-deferred list.
- Full design + resolved reference + clarification question for Matan:
  `docs/CONTEXT_HIJACKING_REPRODUCTION_REPORT.md`.

**Reference is UNCONFIRMED.** Leading candidate = In-Context Representation Hijacking /
Doublespeak (arXiv 2512.03771, Yona et al.); released code (verified reachable):
https://github.com/1tux/doublespeak (MIT). Do not claim it is definitely Matan's paper
until confirmed.

Reuse (do not re-implement):
- Loaders: `poc_stage4/qwen3_model.py`, `poc_stage4/model_family_utils.py`.
- Frozen eval: `poc_stage3/strongreject_scoring.py` (success = strongreject_score >= 0.5).
- Output schema: `schemas/sprint_unified_result.schema.json`.
- Activation infra: `poc_stage4/activation_capture.py`, `poc_stage_ae/replay_hidden_states.py`.
