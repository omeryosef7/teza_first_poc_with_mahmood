"""
Stage 4.6 — Build controlled ablation prompts.

Selects 1 source example per goal_index (4 goals) from usable Stage 4 traces,
then produces 5 prompt conditions per source:

  A — full prompt, thinking=True   (identity copy of source)
  B — ~50% puzzle tokens kept, thinking=True
  C — ~25% puzzle tokens kept, thinking=True
  D — no puzzle tokens, thinking=True   (target + answer cue + chat template only)
  E — full prompt, thinking=False  (identity copy, thinking disabled)

Puzzle wrapper = prompt tokens that are NOT part of:
  - chat template special tokens
  - the embedded harmful target span
  - the answer/execution cue span

Span identification uses exact string-match of goal text (embedded target) and
the final imperative sentence (answer cue) within the formatted prompt.

Usage:
  python -m poc_stage4_6.build_controlled_ablation_prompts [--dry-run] [--output-dir PATH]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage4_5 import common

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONDITIONS: list[str] = ["A", "B", "C", "D", "E"]
PUZZLE_FRACTIONS: dict[str, float | None] = {
    "A": 1.0,
    "B": 0.50,
    "C": 0.25,
    "D": 0.0,
    "E": 1.0,  # same as A, thinking disabled
}
THINKING_MODE: dict[str, bool] = {
    "A": True,
    "B": True,
    "C": True,
    "D": True,
    "E": False,
}

ABLATION_PROMPTS_FIELDNAMES = [
    "source_example_id",
    "condition",
    "goal_index",
    "attack_iteration",
    "conversation_id",
    "target_model",
    "enable_thinking",
    "puzzle_fraction_target",
    "puzzle_tokens_total",
    "puzzle_tokens_kept",
    "prompt_token_count",
    "prompt_token_ids_sha256",
    "target_span_sha256",
    "answer_cue_span_sha256",
    "condition_a_sha256",
    "source_prompt_sha256",
    "validation_passed",
    "validation_notes",
]

_STAGE2_JSONL = (
    _REPO_ROOT / "outputs" / "hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl"
)
_PILOT_QUEUE = _REPO_ROOT / "review" / "pilot_example_queue.csv"
_OUTPUT_BASE = _REPO_ROOT / "outputs" / "stage4_6"


# ---------------------------------------------------------------------------
# Source-prompt selection (deterministic, seed=42)
# ---------------------------------------------------------------------------

def load_stage2_rows() -> dict[tuple[int, int, int], dict]:
    """Return dict keyed by (goal_index, attack_iteration, conversation_id)."""
    rows: dict[tuple[int, int, int], dict] = {}
    with open(_STAGE2_JSONL, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            key = (
                int(r.get("goal_index", -1)),
                int(r.get("attack_iteration", -1)),
                int(r.get("conversation_id", -1)),
            )
            if key not in rows:
                rows[key] = r
    return rows


def _parse_example_id(eid: str) -> dict[str, Any]:
    parts = {}
    for seg in eid.split("|"):
        k, _, v = seg.partition("=")
        parts[k] = v
    return parts


def select_source_examples(rng: random.Random) -> list[dict]:
    dataset = common.load_analysis_dataset()
    pilot_ids: set[str] = set()
    if _PILOT_QUEUE.exists():
        for r in common.read_csv_as_list(_PILOT_QUEUE):
            eid = r.get("example_id", "")
            if eid:
                pilot_ids.add(eid)

    usable = [
        r for r in dataset
        if r["thinking_segmentation_status"] == "parsed_from_think_tags"
        and not r["right_censored"]
    ]

    selected: dict[int, dict] = {}
    for goal_index in range(4):
        candidates = [r for r in usable if r["goal_index"] == goal_index]
        if not candidates:
            raise RuntimeError(f"No usable examples for goal_index={goal_index}")
        # prefer pilot examples, then sort by conversation_id
        pilot_candidates = [r for r in candidates if r["example_id"] in pilot_ids]
        pool = pilot_candidates if pilot_candidates else candidates
        pool.sort(key=lambda r: r["conversation_id"])
        selected[goal_index] = pool[0]

    return [selected[i] for i in range(4)]


# ---------------------------------------------------------------------------
# Token span identification
# ---------------------------------------------------------------------------

def _sha256_of_token_ids(token_ids: list[int]) -> str:
    h = hashlib.sha256()
    h.update(json.dumps(token_ids, separators=(",", ":")).encode())
    return h.hexdigest()


def _find_subseq(seq: list[int], sub: list[int]) -> int | None:
    """Return start index (into seq) of first occurrence of sub, or None."""
    if not sub or len(seq) < len(sub):
        return None
    slen = len(sub)
    for i in range(len(seq) - slen + 1):
        if seq[i : i + slen] == sub:
            return i
    return None


def identify_spans(
    trace: dict,
    stage2_row: dict,
) -> dict[str, Any]:
    """
    Identify prompt token index ranges for:
      - chat_template_tokens: special tokens (is_special_token=True)
      - embedded_target_span: tokens encoding the goal text fragment
      - answer_cue_span: last 2–3 sentences of the attack_prompt
      - puzzle_wrapper_span: all other non-special prompt tokens

    Returns dict with span information and validation flags.
    """
    token_table = trace.get("token_table", [])
    prompt_tokens = [t for t in token_table if t["segment"] == "prompt"]
    prompt_token_ids = [t["token_id"] for t in prompt_tokens]
    prompt_token_strs = [t["decoded_single_token"] for t in prompt_tokens]
    n = len(prompt_tokens)

    # Reconstruct prompt text from token strings (non-special)
    prompt_text = "".join(
        t["decoded_single_token"]
        for t in prompt_tokens
        if not t["is_special_token"]
    )

    attack_prompt: str = stage2_row.get("attack_prompt", "")
    goal: str = stage2_row.get("goal", "")

    # --- answer cue span ---
    # The last paragraph(s) of the attack_prompt serve as the answer cue.
    # Use the last sentence/paragraph that starts after the last blank line.
    answer_cue_text = _extract_answer_cue(attack_prompt)

    # --- embedded target hint ---
    # The goal text is partially embedded in the puzzle via variable naming
    # (e.g., goal keywords appear near the middle of the attack_prompt).
    # Use the middle 30% of the attack prompt as the target region heuristic.
    target_hint_text = _extract_target_hint(attack_prompt)

    # Find char offsets for answer cue and target hint in prompt_text
    answer_cue_char_start = prompt_text.rfind(answer_cue_text[:60])
    target_hint_char_start = prompt_text.find(target_hint_text[:60])

    # Build char→token_index map
    char_to_token: list[int] = []
    pos = 0
    for i, t in enumerate(prompt_tokens):
        if not t["is_special_token"]:
            for _ in t["decoded_single_token"]:
                char_to_token.append(i)
            pos += len(t["decoded_single_token"])
        else:
            char_to_token.append(i)

    def char_to_tok_idx(char_pos: int) -> int:
        if char_pos < 0:
            return 0
        if char_pos >= len(char_to_token):
            return n - 1
        return char_to_token[char_pos]

    # Compute span boundaries (in prompt token indices)
    answer_cue_tok_start = char_to_tok_idx(answer_cue_char_start) if answer_cue_char_start >= 0 else max(0, n - 50)
    answer_cue_tok_end = n  # through end of prompt

    target_hint_tok_start = char_to_tok_idx(target_hint_char_start) if target_hint_char_start >= 0 else n // 3
    target_hint_len_chars = len(target_hint_text)
    target_hint_tok_end = char_to_tok_idx(target_hint_char_start + target_hint_len_chars) if target_hint_char_start >= 0 else (n // 3 + 30)

    # Special tokens
    special_token_indices: set[int] = {
        i for i, t in enumerate(prompt_tokens) if t["is_special_token"]
    }

    # Protected = special tokens ∪ target hint span ∪ answer cue span
    protected_indices: set[int] = set(special_token_indices)
    protected_indices.update(range(target_hint_tok_start, target_hint_tok_end))
    protected_indices.update(range(answer_cue_tok_start, answer_cue_tok_end))

    # Puzzle wrapper = all prompt token indices not in protected
    puzzle_indices: list[int] = sorted(i for i in range(n) if i not in protected_indices)

    target_span_ids = [prompt_tokens[i]["token_id"] for i in range(target_hint_tok_start, target_hint_tok_end)]
    answer_cue_ids = [prompt_tokens[i]["token_id"] for i in range(answer_cue_tok_start, answer_cue_tok_end)]

    # Identify user-message content token range:
    # Qwen3 chat template: <|im_start|>(0) user(1) \n(2) {content...} <|im_end|>(n-5) \n(n-4) <|im_start|>(n-3) assistant(n-2) \n(n-1)
    # Content indices = [3 .. n-6] inclusive (everything excluding 5-token suffix)
    content_start_idx = 3
    content_end_idx = n - 5  # exclusive upper bound for suffix (last 5 are template)

    return {
        "prompt_tokens": prompt_tokens,
        "prompt_token_ids": prompt_token_ids,
        "n_prompt_tokens": n,
        "special_token_indices": sorted(special_token_indices),
        "target_span": (target_hint_tok_start, target_hint_tok_end),
        "answer_cue_span": (answer_cue_tok_start, answer_cue_tok_end),
        "puzzle_indices": puzzle_indices,
        "target_span_ids": target_span_ids,
        "answer_cue_ids": answer_cue_ids,
        "target_span_sha256": _sha256_of_token_ids(target_span_ids),
        "answer_cue_span_sha256": _sha256_of_token_ids(answer_cue_ids),
        "full_prompt_sha256": _sha256_of_token_ids(prompt_token_ids),
        "answer_cue_text": answer_cue_text,
        "target_hint_text": target_hint_text,
        "answer_cue_char_start": answer_cue_char_start,
        "target_hint_char_start": target_hint_char_start,
        "content_start_idx": content_start_idx,
        "content_end_idx": content_end_idx,
    }


def _extract_answer_cue(attack_prompt: str) -> str:
    """Extract the last paragraph of the attack prompt as the answer cue."""
    paragraphs = [p.strip() for p in attack_prompt.split("\n\n") if p.strip()]
    if not paragraphs:
        return attack_prompt[-200:]
    last = paragraphs[-1]
    # Return last paragraph (up to 500 chars)
    return last[:500]


def _extract_target_hint(attack_prompt: str) -> str:
    """Extract the middle portion of the attack prompt containing the target encoding."""
    n = len(attack_prompt)
    start = n // 4
    end = 3 * n // 4
    # Find the paragraph boundaries closest to these positions
    segment = attack_prompt[start:end]
    return segment[:300]


# ---------------------------------------------------------------------------
# Condition builders
# ---------------------------------------------------------------------------

def build_condition(
    condition: str,
    span_info: dict,
    puzzle_fraction: float,
    rng: random.Random,
) -> dict[str, Any]:
    """
    Build one ablation condition.

    Returns dict with:
      - token_ids: list[int] (the prompt token id sequence for this condition)
      - token_strings: list[str]
      - enable_thinking: bool
      - puzzle_tokens_kept: int
      - puzzle_tokens_total: int
      - validation_passed: bool
      - validation_notes: list[str]
    """
    prompt_tokens = span_info["prompt_tokens"]
    puzzle_indices = span_info["puzzle_indices"]
    n = span_info["n_prompt_tokens"]
    enable_thinking = THINKING_MODE[condition]
    notes: list[str] = []

    if condition == "A" or condition == "E":
        # Identity copy — keep all tokens
        kept_indices = set(range(n))
        puzzle_kept = len(puzzle_indices)
    else:
        # Delete puzzle tokens to reach target fraction
        target_kept = max(0, round(puzzle_fraction * len(puzzle_indices)))
        # Keep evenly-spaced puzzle tokens (deterministic)
        if target_kept == 0 or not puzzle_indices:
            kept_puzzle = []
        elif target_kept >= len(puzzle_indices):
            kept_puzzle = puzzle_indices
        else:
            step = len(puzzle_indices) / target_kept
            kept_puzzle = [puzzle_indices[round(i * step)] for i in range(target_kept)]
        kept_indices = set(range(n)) - (set(puzzle_indices) - set(kept_puzzle))
        puzzle_kept = len(kept_puzzle)

    # Build output token sequences (maintain original order)
    output_token_ids = [
        prompt_tokens[i]["token_id"]
        for i in range(n)
        if i in kept_indices
    ]
    output_token_strs = [
        prompt_tokens[i]["decoded_single_token"]
        for i in range(n)
        if i in kept_indices
    ]

    # --- Validation ---
    validation_passed = True

    # 1. Target span tokens preserved
    target_start, target_end = span_info["target_span"]
    target_ids_in_output = [
        prompt_tokens[i]["token_id"]
        for i in range(target_start, target_end)
        if i in kept_indices
    ]
    if target_ids_in_output != span_info["target_span_ids"]:
        notes.append("FAIL: target span not fully preserved")
        validation_passed = False

    # 2. Answer cue tokens preserved
    acue_start, acue_end = span_info["answer_cue_span"]
    acue_ids_in_output = [
        prompt_tokens[i]["token_id"]
        for i in range(acue_start, acue_end)
        if i in kept_indices
    ]
    if acue_ids_in_output != span_info["answer_cue_ids"]:
        notes.append("FAIL: answer cue span not fully preserved")
        validation_passed = False

    # 3. Deletion-only: output is a subsequence of source
    # (guaranteed by construction since we only remove tokens)

    # 4. Output not empty
    if not output_token_ids:
        notes.append("FAIL: empty output token sequence")
        validation_passed = False

    if validation_passed:
        notes.append("OK")

    # Reconstruct user-message text from kept content tokens
    # (non-template, non-special tokens in range [content_start, content_end])
    cs = span_info.get("content_start_idx", 3)
    ce = span_info.get("content_end_idx", n - 5)
    user_message_text = "".join(
        prompt_tokens[i]["decoded_single_token"]
        for i in range(n)
        if i in kept_indices and cs <= i <= ce and not prompt_tokens[i]["is_special_token"]
    )

    return {
        "token_ids": output_token_ids,
        "token_strings": output_token_strs,
        "enable_thinking": enable_thinking,
        "puzzle_tokens_kept": puzzle_kept,
        "puzzle_tokens_total": len(puzzle_indices),
        "prompt_token_count": len(output_token_ids),
        "prompt_token_ids_sha256": _sha256_of_token_ids(output_token_ids),
        "user_message_text": user_message_text,
        "validation_passed": validation_passed,
        "validation_notes": notes,
    }


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_ablation_prompts(
    dry_run: bool = False,
    output_dir: Path | None = None,
) -> list[dict]:
    rng = random.Random(42)
    out_dir = output_dir or _OUTPUT_BASE
    out_dir.mkdir(parents=True, exist_ok=True)

    stage2_rows = load_stage2_rows()
    sources = select_source_examples(rng)

    print(f"Selected {len(sources)} source examples:")
    for s in sources:
        print(f"  goal={s['goal_index']} → {s['example_id']}")

    # Write prompt_selection.csv
    sel_csv_path = out_dir / "prompt_selection.csv"
    if not dry_run:
        common.write_csv(sel_csv_path, sources, list(sources[0].keys()))
        print(f"Wrote {sel_csv_path}")

    all_rows: list[dict] = []
    all_passed = True

    for meta in sources:
        eid = meta["example_id"]
        parsed = _parse_example_id(eid)
        goal_index = int(parsed.get("goal_index", meta["goal_index"]))
        attack_iteration = int(parsed.get("attack_iteration", meta["attack_iteration"]))
        conversation_id = int(parsed.get("conversation_id", meta["conversation_id"]))
        target_model = parsed.get("target_model", meta.get("target_model", ""))

        s2_key = (goal_index, attack_iteration, conversation_id)
        stage2_row = stage2_rows.get(s2_key)
        if stage2_row is None:
            raise RuntimeError(f"No stage2 row for {s2_key}")

        try:
            trace = common.load_stage6_trace(eid)
        except FileNotFoundError:
            raise RuntimeError(f"Stage6 trace not found for {eid}")

        span_info = identify_spans(trace, stage2_row)
        n_puzzle = len(span_info["puzzle_indices"])
        n_prompt = span_info["n_prompt_tokens"]
        print(
            f"\n  [{eid}] prompt_tokens={n_prompt} puzzle_tokens={n_puzzle} "
            f"target_span={span_info['target_span']} answer_cue_span={span_info['answer_cue_span']}"
        )

        if n_puzzle == 0:
            raise RuntimeError(f"No puzzle tokens identified for {eid} — cannot ablate")

        condition_a_result = build_condition("A", span_info, 1.0, rng)
        source_sha256 = span_info["full_prompt_sha256"]
        condition_a_sha256 = condition_a_result["prompt_token_ids_sha256"]

        if condition_a_sha256 != source_sha256:
            print(f"  WARNING: condition A sha256 != source sha256 — possible token mismatch")

        prev_token_count: int | None = None

        for cond in CONDITIONS:
            frac = PUZZLE_FRACTIONS[cond]
            result = build_condition(cond, span_info, frac if frac is not None else 1.0, rng)

            tok_count = result["prompt_token_count"]

            # Check monotonic decrease (A ≥ B ≥ C ≥ D; E == A is fine)
            if cond not in ("A", "E"):
                if prev_token_count is not None and tok_count > prev_token_count:
                    result["validation_notes"].append(
                        f"WARN: token count {tok_count} > previous {prev_token_count} (not monotone)"
                    )

            if cond not in ("E",):
                prev_token_count = tok_count

            if not result["validation_passed"]:
                all_passed = False
                print(f"  FAIL condition {cond}: {result['validation_notes']}")
            else:
                print(f"  condition {cond}: {tok_count} tokens, thinking={result['enable_thinking']}, puzzle_kept={result['puzzle_tokens_kept']}/{result['puzzle_tokens_total']}")

            row: dict = {
                "source_example_id": eid,
                "condition": cond,
                "goal_index": goal_index,
                "attack_iteration": attack_iteration,
                "conversation_id": conversation_id,
                "target_model": target_model,
                "enable_thinking": result["enable_thinking"],
                "puzzle_fraction_target": PUZZLE_FRACTIONS[cond],
                "puzzle_tokens_total": result["puzzle_tokens_total"],
                "puzzle_tokens_kept": result["puzzle_tokens_kept"],
                "prompt_token_count": result["prompt_token_count"],
                "prompt_token_ids_sha256": result["prompt_token_ids_sha256"],
                "target_span_sha256": span_info["target_span_sha256"],
                "answer_cue_span_sha256": span_info["answer_cue_span_sha256"],
                "condition_a_sha256": condition_a_sha256,
                "source_prompt_sha256": source_sha256,
                "validation_passed": result["validation_passed"],
                "validation_notes": "; ".join(result["validation_notes"]),
                # Runtime fields for the runner (stored in JSONL, not CSV)
                "_token_ids": result["token_ids"],
                "_token_strings": result["token_strings"],
                "_user_message_text": result["user_message_text"],
                "_goal": stage2_row.get("goal", ""),
                "_attack_prompt": stage2_row.get("attack_prompt", ""),
            }
            all_rows.append(row)

    # Write ablation_prompts.jsonl (no raw harmful text — only token ids + metadata)
    jsonl_path = out_dir / "ablation_prompts.jsonl"
    if not dry_run:
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for row in all_rows:
                # Exclude _attack_prompt from the file (no raw harmful text)
                safe_row = {k: v for k, v in row.items() if k != "_attack_prompt"}
                f.write(json.dumps(safe_row, separators=(",", ":")) + "\n")
        print(f"\nWrote {jsonl_path} ({len(all_rows)} rows)")

    # Write manifest
    manifest = {
        "created_utc": common.utc_now(),
        "n_sources": len(sources),
        "n_conditions": len(CONDITIONS),
        "n_rows": len(all_rows),
        "conditions": CONDITIONS,
        "all_validations_passed": all_passed,
        "do_sample": False,
        "generation_is_deterministic": True,
        "seed": 42,
        "model_name_or_path": "Qwen/Qwen3-14B",
        "model_revision": "40c069824f4251a91eefaf281ebe4c544efd3e18",
    }
    manifest_path = out_dir / "prompt_selection_manifest.json"
    if not dry_run:
        common.atomic_write_json(manifest_path, manifest)
        print(f"Wrote {manifest_path}")

    if not all_passed:
        print("\nERROR: some validation checks failed — review notes above")
        sys.exit(1)

    print(f"\nAll {len(all_rows)} ablation prompts validated OK.")
    return all_rows


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build Stage 4.6 controlled ablation prompts.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--dry-run", action="store_true", default=False)
    p.add_argument("--output-dir", type=Path, default=None)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    build_ablation_prompts(dry_run=args.dry_run, output_dir=args.output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
