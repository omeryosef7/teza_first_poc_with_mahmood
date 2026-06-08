"""
Stage 4.5 — Phase 2: Interactive harmful-interaction event annotation CLI.

Displays generated tokens in paginated blocks and allows the reviewer to set
the generated_token_index at which the model's thinking first engages with
the embedded harmful target.

Any generated token (think, special, or final) may be annotated.  The
primary analysis uses think-phase events; final-phase events are retained for
sensitivity analysis.

Writes to (appends/updates):
  review/harmful_interaction_annotations.csv

Usage:
  python -m poc_stage4_5.annotate_harmful_interaction [--example-id ID] [options]

  Omit --example-id to pick the next pending example from the annotation queue.

Commands during annotation:
  n      — show next block of tokens
  p      — show previous block
  j N    — jump to block containing token N
  s N    — set harmful_interaction_start_token to generated_token_index N
  done   — finish (requires event to be set or a status flag)
  none   — mark as no_harmful_interaction_found
  unc    — mark as uncertain
  skip   — skip without saving (defer to later)
  show   — toggle full token text visibility
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage4_5 import common

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

ANNOTATIONS_FIELDNAMES: list[str] = [
    "example_id",
    "annotation_timestamp_utc",
    "harmful_interaction_start_token",  # generated_token_index; -1 if none
    "annotation_confidence",            # renamed from annotator_confidence
    "interaction_phase",                # role_or_part of the onset token
    "annotation_notes",
    "annotator_id",
    "annotation_status",                # annotated / no_harmful_interaction_found / uncertain
    # optional extended fields (empty for basic annotations)
    "harmful_interaction_end_token",
    "final_answer_start_token",
    "decision_or_commitment_candidate_token",
    "right_censored",
    "segmentation_complete",
]

_BLOCK_SIZE = 50  # tokens per display block


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _display_block(tokens: list[dict], block_idx: int, show_text: bool) -> None:
    start = block_idx * _BLOCK_SIZE
    end = min(start + _BLOCK_SIZE, len(tokens))
    block = tokens[start:end]

    print(f"\n--- Block {block_idx + 1} / {(len(tokens) + _BLOCK_SIZE - 1) // _BLOCK_SIZE} "
          f"(tokens {start}–{end - 1} of {len(tokens)} generated) ---")
    for tok in block:
        gidx = tok["generated_token_index"]
        role = tok.get("role_or_part", "?")
        tok_id = tok.get("token_id", "?")
        if show_text:
            text = tok.get("token_text", "")
        else:
            text = tok.get("token_text", "")[:30]
        special = " [SPECIAL]" if tok.get("is_special_token") else ""
        print(f"  [{gidx:5d}] {role:7s}{special}  text={text!r}")
    print()


def _display_header(example_id: str, meta: dict, current_set: int | None) -> None:
    sep = "=" * 72
    print(sep)
    print(f"  EXAMPLE : {example_id}")
    print(f"  Goal: {meta.get('goal_index')} | Iter: {meta.get('attack_iteration')} | "
          f"Conv: {meta.get('conversation_id')}")
    print(f"  SR: {float(meta.get('strongreject_score', 0)):.3f}  "
          f"sr_success={meta.get('sr_success')}  "
          f"Gemini={meta.get('judge_score')} judge_success={meta.get('judge_success')}")
    print(f"  Think tokens: {meta.get('think_token_count')}  "
          f"Generation total: {meta.get('generation_token_count')}  "
          f"Right-censored: {meta.get('right_censored')}")
    if current_set is not None:
        print(f"  *** Currently set: harmful_interaction_start_token = {current_set} ***")
    else:
        print("  (No event token set yet)")
    print(sep)


# ---------------------------------------------------------------------------
# Annotation interaction loop
# ---------------------------------------------------------------------------

def _annotate_interactive(
    example_id: str,
    tokens: list[dict],
    meta: dict,
    existing: dict | None,
) -> dict | None:
    """
    Run the interactive annotation loop.

    Returns a completed annotation dict, or None if the reviewer chose to skip.
    """
    n_tokens = len(tokens)
    n_blocks = max(1, (n_tokens + _BLOCK_SIZE - 1) // _BLOCK_SIZE)
    block_idx = 0
    current_set: int | None = None
    show_text = True

    # Pre-fill from existing annotation if present
    if existing and existing.get("harmful_interaction_start_token"):
        try:
            current_set = int(existing["harmful_interaction_start_token"])
        except (ValueError, TypeError):
            pass

    print(
        "\nCommands: [n] next block  [p] prev block  [j N] jump to token N  "
        "[s N] set event to N\n"
        "          [done] finish  [none] no harmful interaction  "
        "[unc] uncertain  [skip] defer\n"
        "          [show] toggle token text\n"
    )

    _display_header(example_id, meta, current_set)
    _display_block(tokens, block_idx, show_text)

    while True:
        try:
            cmd_raw = input(">> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nInterrupted — skipping.")
            return None

        if not cmd_raw:
            continue

        parts = cmd_raw.lower().split()
        cmd = parts[0]

        if cmd == "n":
            block_idx = min(block_idx + 1, n_blocks - 1)
            _display_block(tokens, block_idx, show_text)

        elif cmd == "p":
            block_idx = max(block_idx - 1, 0)
            _display_block(tokens, block_idx, show_text)

        elif cmd == "j" and len(parts) >= 2:
            try:
                target = int(parts[1])
            except ValueError:
                print("  Usage: j N  (where N is a generated_token_index)")
                continue
            # Find which block contains that index
            found_block = None
            for i in range(n_blocks):
                s = i * _BLOCK_SIZE
                e = min(s + _BLOCK_SIZE, n_tokens)
                block_tokens = tokens[s:e]
                if any(t["generated_token_index"] == target for t in block_tokens):
                    found_block = i
                    break
            if found_block is not None:
                block_idx = found_block
                _display_block(tokens, block_idx, show_text)
            else:
                print(f"  Token index {target} not found in generated tokens.")

        elif cmd == "s" and len(parts) >= 2:
            try:
                target = int(parts[1])
            except ValueError:
                print("  Usage: s N  (where N is a generated_token_index)")
                continue
            # Validate: must be a real generated_token_index
            valid_indices = {t["generated_token_index"] for t in tokens}
            if target not in valid_indices:
                print(f"  Invalid index {target}. Must be one of the displayed indices.")
                continue
            current_set = target
            _display_header(example_id, meta, current_set)
            print(f"  ✓ Set harmful_interaction_start_token = {current_set}")

        elif cmd == "done":
            if current_set is None:
                print("  No event token is set. Use [s N] to set one, or [none]/[unc].")
                continue
            # Determine interaction_phase from the token's role_or_part
            tok_phase = "unknown"
            for t in tokens:
                if t["generated_token_index"] == current_set:
                    tok_phase = t.get("role_or_part", "unknown")
                    break
            # Collect confidence and notes
            while True:
                conf_raw = input("Confidence (h=high, m=medium, l=low): ").strip().lower()
                if conf_raw in ("h", "m", "l"):
                    break
                print("  Enter h, m, or l.")
            confidence_map = {"h": "high", "m": "medium", "l": "low"}
            notes = input("Annotation notes (press Enter to skip): ").strip()
            annotator_id = input("Annotator ID (press Enter for 'primary'): ").strip() or "primary"

            return {
                "example_id": example_id,
                "annotation_timestamp_utc": common.utc_now(),
                "harmful_interaction_start_token": str(current_set),
                "annotation_confidence": confidence_map[conf_raw],
                "interaction_phase": tok_phase,
                "annotation_notes": notes,
                "annotator_id": annotator_id,
                "annotation_status": "annotated",
            }

        elif cmd in ("none", "no"):
            notes = input("Notes (why no harmful interaction?): ").strip()
            annotator_id = input("Annotator ID (press Enter for 'primary'): ").strip() or "primary"
            return {
                "example_id": example_id,
                "annotation_timestamp_utc": common.utc_now(),
                "harmful_interaction_start_token": "-1",
                "annotation_confidence": "high",
                "interaction_phase": "none",
                "annotation_notes": notes,
                "annotator_id": annotator_id,
                "annotation_status": "no_harmful_interaction_found",
            }

        elif cmd == "unc":
            notes = input("Notes (why uncertain?): ").strip()
            annotator_id = input("Annotator ID (press Enter for 'primary'): ").strip() or "primary"
            current_str = str(current_set) if current_set is not None else "-1"
            return {
                "example_id": example_id,
                "annotation_timestamp_utc": common.utc_now(),
                "harmful_interaction_start_token": current_str,
                "annotation_confidence": "low",
                "interaction_phase": "uncertain",
                "annotation_notes": notes,
                "annotator_id": annotator_id,
                "annotation_status": "uncertain",
            }

        elif cmd == "skip":
            print("  Skipped — no annotation saved.")
            return None

        elif cmd == "show":
            show_text = not show_text
            print(f"  Token text display: {'ON' if show_text else 'OFF'}")
            _display_block(tokens, block_idx, show_text)

        elif cmd in ("h", "help", "?"):
            print(
                "Commands:\n"
                "  n          — next block\n"
                "  p          — previous block\n"
                "  j N        — jump to block containing token index N\n"
                "  s N        — set harmful_interaction_start_token to N\n"
                "  done       — finish annotation (event must be set)\n"
                "  none       — mark as no_harmful_interaction_found\n"
                "  unc        — mark as uncertain\n"
                "  skip       — defer without saving\n"
                "  show       — toggle token text display\n"
            )
        else:
            print("  Unknown command. Type 'h' for help.")


# ---------------------------------------------------------------------------
# Core workflow
# ---------------------------------------------------------------------------

def _load_existing_annotation(example_id: str, annotations_path: Path) -> dict | None:
    if not annotations_path.exists():
        return None
    rows = common.read_csv_as_list(annotations_path)
    for r in rows:
        if r.get("example_id") == example_id:
            return r
    return None


def _pick_next_pending(review_dir: Path, analysis_dataset_path: Path) -> str | None:
    """Return the next example_id that is pending annotation, or None."""
    from poc_stage4_5.build_event_annotation_queue import build_annotation_queue
    progress_path = review_dir / "manual_adjudication_progress.csv"
    annotations_path = review_dir / "harmful_interaction_annotations.csv"
    queue = build_annotation_queue(analysis_dataset_path, progress_path, annotations_path)
    for row in queue:
        if row["annotation_status"] == "pending":
            return row["example_id"]
    return None


def annotate_one(
    example_id: str,
    review_dir: Path,
    analysis_dataset_path: Path,
    force: bool,
) -> int:
    """Annotate one example. Returns 0 on success."""
    annotations_path = review_dir / "harmful_interaction_annotations.csv"

    existing = _load_existing_annotation(example_id, annotations_path)
    if existing and not force:
        print(f"Example {example_id!r} is already annotated:")
        print(f"  Status: {existing.get('annotation_status')}  "
              f"token={existing.get('harmful_interaction_start_token')}  "
              f"phase={existing.get('interaction_phase')}")
        ans = input("Re-annotate and overwrite? (y/N): ").strip().lower()
        if ans != "y":
            print("Skipping.")
            return 0

    # Load metadata
    dataset = common.load_analysis_dataset(analysis_dataset_path)
    meta_map = {r["example_id"]: r for r in dataset}
    if example_id not in meta_map:
        print(f"ERROR: {example_id!r} not found in analysis_dataset.", file=sys.stderr)
        return 1
    meta = meta_map[example_id]

    # Structural blocks
    seg_status = meta.get("thinking_segmentation_status", "")
    right_censored = meta.get("right_censored", False)
    if seg_status != "parsed_from_think_tags":
        print(f"  This example is not separable (segmentation_status={seg_status!r}).")
        print("  Saving as 'not_separable'.")
        ann = {
            "example_id": example_id,
            "annotation_timestamp_utc": common.utc_now(),
            "harmful_interaction_start_token": "-1",
            "annotation_confidence": "high",
            "interaction_phase": "none",
            "annotation_notes": "not_separable",
            "annotator_id": "auto",
            "annotation_status": "not_separable",
        }
    elif right_censored:
        print(f"  This example is right-censored.")
        ans = input("Proceed with partial annotation? (y/N): ").strip().lower()
        if ans != "y":
            print("Skipping.")
            return 0
        ann = None  # will be set by interactive annotation below
    else:
        ann = None

    if ann is None:
        # Load per-example JSON tokens for display
        try:
            artifact = common.load_stage4_per_example(example_id)
        except FileNotFoundError:
            print(f"ERROR: Stage 4 per-example artifact not found for {example_id!r}.",
                  file=sys.stderr)
            return 1

        tokens = artifact.get("token_level_data", [])
        if not tokens:
            print("ERROR: No token_level_data in artifact.", file=sys.stderr)
            return 1

        ann = _annotate_interactive(example_id, tokens, meta, existing)
        if ann is None:
            print("No annotation saved (skipped).")
            return 0

    # Save: if overwriting, replace existing row
    if existing:
        all_rows = common.read_csv_as_list(annotations_path) if annotations_path.exists() else []
        updated = [r for r in all_rows if r.get("example_id") != example_id]
        updated.append(ann)
        common.write_csv(annotations_path, updated, ANNOTATIONS_FIELDNAMES)
    else:
        common.append_csv_row(annotations_path, ann, ANNOTATIONS_FIELDNAMES)

    print(f"\n✓ Annotation saved: token={ann['harmful_interaction_start_token']}  "
          f"phase={ann['interaction_phase']}  "
          f"status={ann['annotation_status']}")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Stage 4.5 interactive harmful-interaction event annotation CLI.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--example-id",
        default=None,
        help="Example ID to annotate (omit to pick next pending).",
    )
    p.add_argument(
        "--review-dir",
        type=Path,
        default=common.DEFAULT_REVIEW_DIR,
    )
    p.add_argument(
        "--analysis-dataset",
        type=Path,
        default=common.ANALYSIS_DATASET_PATH,
    )
    p.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Overwrite existing annotation without prompting.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    example_id = args.example_id
    if example_id is None:
        example_id = _pick_next_pending(args.review_dir, args.analysis_dataset)
        if example_id is None:
            print("All examples are annotated or excluded. Nothing to do.")
            return 0
        print(f"Auto-selected next pending example: {example_id!r}")

    return annotate_one(
        example_id=example_id,
        review_dir=args.review_dir,
        analysis_dataset_path=args.analysis_dataset,
        force=args.force,
    )


if __name__ == "__main__":
    sys.exit(main())
