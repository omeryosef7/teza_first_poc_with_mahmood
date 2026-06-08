"""
Stage 4.5 — Phase 5B stub: Analyze captured attention weights from pilot.

**NOT APPROVED FOR EXECUTION.**

Requires captured attention tensors from capture_attention_pilot.py,
which is itself blocked until the methodology audit is complete.

See docs/STAGE4_5_ATTENTION_METHOD_AUDIT.md for methodology audit status.

Implementation notes (to fill when capture is complete):
  - Load per-example .pt attention tensors
  - Aggregate over heads (method TBD per audit Q3)
  - Compute per-span attention trajectories relative to harmful-interaction onset
  - Run Mann-Whitney U test: attention to embedded_harmful_goal_span in pre vs. post window
  - Produce plots: attention-to-span over generation for success vs. failure
  - Write event_aligned_attention_summary.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


AUDIT_BLOCK_MESSAGE = (
    "BLOCKED: analyze_attention_pilot.py requires captured attention tensors from "
    "capture_attention_pilot.py, which is blocked on the methodology audit. "
    "See docs/STAGE4_5_ATTENTION_METHOD_AUDIT.md."
)


def main(argv: list[str] | None = None) -> int:
    print(AUDIT_BLOCK_MESSAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
