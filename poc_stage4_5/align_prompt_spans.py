"""
Stage 4.5 — Phase 5A: Map named prompt segments to token index ranges.

Takes a Stage 6 trace (which contains prompt_token_ids and the raw prompt text components)
and caller-supplied span text definitions, and finds the start/end token-index boundaries
of each span using subsequence matching.

Named spans:
  puzzle_span                     — the puzzle / reasoning task portion
  embedded_harmful_goal_span      — the injected harmful instruction
  answer_or_execution_cue_span    — the cue to answer / execute
  chat_template_and_special_tokens — chat template delimiters and special tokens
  prior_generated_reasoning_span  — prior assistant turn (absent in single-turn attacks)
  other_prompt_span               — remaining tokens not covered above

Output: span_alignment.json per example

Usage:
  python -m poc_stage4_5.align_prompt_spans \\
      --example-id EXAMPLE_ID \\
      --span-definitions spans.json \\
      --output-dir <dir>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage4_5 import common

# ---------------------------------------------------------------------------
# Span names
# ---------------------------------------------------------------------------

NAMED_SPANS = [
    "puzzle_span",
    "embedded_harmful_goal_span",
    "answer_or_execution_cue_span",
    "chat_template_and_special_tokens",
    "prior_generated_reasoning_span",
    "other_prompt_span",
]


# ---------------------------------------------------------------------------
# Subsequence search (validated algorithm from diagnose_reasoning_visible_tokens.py)
# ---------------------------------------------------------------------------

def find_subsequence(sequence: list[int], subsequence: list[int]) -> int | None:
    """Return start index of first occurrence of subsequence in sequence, or None."""
    if not subsequence or len(sequence) < len(subsequence):
        return None
    sub_len = len(subsequence)
    for start in range(len(sequence) - sub_len + 1):
        if sequence[start : start + sub_len] == subsequence:
            return start
    return None


def find_all_occurrences(sequence: list[int], subsequence: list[int]) -> list[int]:
    """Return all start positions of subsequence in sequence."""
    if not subsequence or len(sequence) < len(subsequence):
        return []
    results = []
    sub_len = len(subsequence)
    for start in range(len(sequence) - sub_len + 1):
        if sequence[start : start + sub_len] == subsequence:
            results.append(start)
    return results


# ---------------------------------------------------------------------------
# Core alignment function
# ---------------------------------------------------------------------------

def align_span(
    prompt_token_ids: list[int],
    span_token_ids: list[int],
    span_name: str,
    allow_absent: bool = False,
) -> dict[str, Any]:
    """
    Find the token-index range of span_token_ids within prompt_token_ids.

    Returns a dict with:
      span_name, status, start_token_index, end_token_index (exclusive),
      n_tokens, occurrences, warning

    status values:
      aligned          — unique match found
      ambiguous        — multiple matches found (alignment not reliable)
      absent           — span not found (only valid if allow_absent=True, else error)
      empty_span       — span_token_ids is empty
      error            — unexpected state
    """
    if not span_token_ids:
        return {
            "span_name": span_name,
            "status": "empty_span",
            "start_token_index": None,
            "end_token_index": None,
            "n_tokens": 0,
            "occurrences": 0,
            "warning": "span_token_ids is empty",
        }

    occurrences = find_all_occurrences(prompt_token_ids, span_token_ids)
    n_occ = len(occurrences)

    if n_occ == 0:
        if allow_absent:
            return {
                "span_name": span_name,
                "status": "absent",
                "start_token_index": None,
                "end_token_index": None,
                "n_tokens": 0,
                "occurrences": 0,
                "warning": "span not found in prompt_token_ids",
            }
        raise ValueError(
            f"Span {span_name!r} not found in prompt_token_ids "
            f"(span length: {len(span_token_ids)}, prompt length: {len(prompt_token_ids)})"
        )

    if n_occ > 1:
        return {
            "span_name": span_name,
            "status": "ambiguous",
            "start_token_index": occurrences[0],
            "end_token_index": occurrences[0] + len(span_token_ids),
            "n_tokens": len(span_token_ids),
            "occurrences": n_occ,
            "warning": f"ambiguous: {n_occ} occurrences found; using first match",
        }

    start = occurrences[0]
    return {
        "span_name": span_name,
        "status": "aligned",
        "start_token_index": start,
        "end_token_index": start + len(span_token_ids),
        "n_tokens": len(span_token_ids),
        "occurrences": 1,
        "warning": None,
    }


def align_all_spans(
    prompt_token_ids: list[int],
    span_definitions: dict[str, list[int]],
) -> dict[str, dict[str, Any]]:
    """
    Align all named spans.  span_definitions maps span_name -> list of token IDs.
    prior_generated_reasoning_span is allowed to be absent (single-turn attacks).
    Returns dict mapping span_name -> alignment result.
    """
    results = {}
    for span_name, token_ids in span_definitions.items():
        allow_absent = span_name == "prior_generated_reasoning_span"
        try:
            results[span_name] = align_span(prompt_token_ids, token_ids, span_name, allow_absent=allow_absent)
        except ValueError as e:
            results[span_name] = {
                "span_name": span_name,
                "status": "error",
                "start_token_index": None,
                "end_token_index": None,
                "n_tokens": 0,
                "occurrences": 0,
                "warning": str(e),
            }
    return results


def compute_other_span(
    prompt_len: int,
    alignments: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """
    Compute other_prompt_span as the complement of all aligned spans.
    Returns a list of (start, end) pairs for uncovered token ranges.
    """
    covered = set()
    for span_name, result in alignments.items():
        if span_name == "other_prompt_span":
            continue
        if result["status"] in ("aligned", "ambiguous") and result["start_token_index"] is not None:
            for i in range(result["start_token_index"], result["end_token_index"]):
                covered.add(i)
    uncovered = [i for i in range(prompt_len) if i not in covered]
    if not uncovered:
        return {
            "span_name": "other_prompt_span",
            "status": "empty_span",
            "uncovered_ranges": [],
            "n_tokens": 0,
            "warning": None,
        }
    # Compress to ranges
    ranges = []
    start_r = uncovered[0]
    prev = uncovered[0]
    for idx in uncovered[1:]:
        if idx != prev + 1:
            ranges.append([start_r, prev + 1])
            start_r = idx
        prev = idx
    ranges.append([start_r, prev + 1])
    return {
        "span_name": "other_prompt_span",
        "status": "aligned",
        "uncovered_ranges": ranges,
        "n_tokens": len(uncovered),
        "warning": None,
    }


# ---------------------------------------------------------------------------
# Per-example workflow
# ---------------------------------------------------------------------------

def align_example(
    example_id: str,
    span_definitions: dict[str, list[int]],
    output_dir: Path,
) -> dict[str, Any]:
    """
    Align prompt spans for one example.  Reads Stage 6 trace, runs alignment,
    writes span_alignment.json to output_dir.
    """
    try:
        trace = common.load_stage6_trace(example_id)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Stage 6 trace not found for {example_id!r}: {e}") from e

    prompt_token_ids = trace.get("prompt_token_ids")
    if not prompt_token_ids:
        raise ValueError(f"No prompt_token_ids in Stage 6 trace for {example_id!r}")

    alignments = align_all_spans(prompt_token_ids, span_definitions)
    alignments["other_prompt_span"] = compute_other_span(len(prompt_token_ids), alignments)

    # Audit
    n_errors = sum(1 for r in alignments.values() if r["status"] == "error")
    n_ambiguous = sum(1 for r in alignments.values() if r["status"] == "ambiguous")
    n_absent = sum(1 for r in alignments.values() if r["status"] == "absent")

    result = {
        "example_id": example_id,
        "prompt_token_count": len(prompt_token_ids),
        "span_alignment_timestamp_utc": common.utc_now(),
        "alignments": alignments,
        "audit": {
            "n_spans_defined": len(span_definitions),
            "n_aligned": sum(1 for r in alignments.values() if r["status"] == "aligned"),
            "n_ambiguous": n_ambiguous,
            "n_absent": n_absent,
            "n_errors": n_errors,
            "warnings": [r["warning"] for r in alignments.values() if r.get("warning")],
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    safe_id = example_id.replace("|", "_").replace("=", "_").replace("/", "_")
    output_path = output_dir / f"{safe_id}_span_alignment.json"
    common.write_json(output_path, common.make_json_safe(result))
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Align named prompt spans to token index ranges (Stage 4.5 Phase 5A).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--example-id", required=True, help="Example ID to align.")
    p.add_argument(
        "--span-definitions",
        type=Path,
        required=True,
        help="JSON file mapping span_name -> list of token IDs.",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=common.DEFAULT_OUTPUT_BASE / "span_alignments",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    span_defs = common.read_json(args.span_definitions)
    result = align_example(args.example_id, span_defs, args.output_dir)
    audit = result["audit"]
    print(f"Aligned {audit['n_aligned']} / {audit['n_spans_defined']} spans for {args.example_id!r}")
    if audit["n_errors"]:
        print(f"  ERRORS: {audit['n_errors']}", file=sys.stderr)
        return 1
    if audit["n_ambiguous"]:
        print(f"  WARNINGS: {audit['n_ambiguous']} ambiguous spans")
    return 0


if __name__ == "__main__":
    sys.exit(main())
