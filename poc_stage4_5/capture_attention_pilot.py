"""
Stage 4.5 — Phase 5B stub: Capture attention weights for pilot examples.

**NOT APPROVED FOR EXECUTION.**

Preconditions before this file may be submitted as a Slurm job:
  1. STAGE4_5_ATTENTION_METHOD_AUDIT.md must answer Q3 (head aggregation),
     Q7 (reported quantity), and Q10 (verified memory estimate).
  2. Memory estimate must be written to manifests/run_manifest.json.
  3. A 2–3 example smoke run must have completed without OOM.
  4. span_alignment.json must exist for all pilot examples.

See docs/STAGE4_5_ATTENTION_METHOD_AUDIT.md for methodology audit status.

Implementation notes (to fill when preconditions are met):
  - Use output_attentions=True in model.generate() or replay-forward with hook capture
  - Capture attention weights per layer per head for prompt tokens during think generation
  - Measure attention from current generated token to each named span
  - Average across think-phase tokens; compute change at harmful-interaction onset
  - Write per-example attention tensors to output_dir/attention_pilot/<example_id>.pt
  - Write per-example summary JSON with mean attention per span per layer
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


AUDIT_BLOCK_MESSAGE = (
    "BLOCKED: capture_attention_pilot.py must not be executed until the methodology "
    "audit and memory estimate are complete. See docs/STAGE4_5_ATTENTION_METHOD_AUDIT.md."
)


def main(argv: list[str] | None = None) -> int:
    print(AUDIT_BLOCK_MESSAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
