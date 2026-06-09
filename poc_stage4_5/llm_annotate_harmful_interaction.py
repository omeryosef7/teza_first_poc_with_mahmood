"""
Stage 4.5B — Automated harmful-interaction onset annotation using o4-mini.

Implements a hierarchical coarse-to-fine two-pass annotation strategy:
  Pass 1 & 2: independently run the full annotation pipeline on each example.
  Consensus:  if both passes agree within ±64 tokens → accept.
  Adjudication: if they disagree → run a third adjudication request.

Outputs under:
  outputs/stage4_5/llm_harmful_interaction_annotations/run_<timestamp>/

Usage:
  # Pilot (10 examples from review/pilot_example_queue.csv):
  python -m poc_stage4_5.llm_annotate_harmful_interaction

  # Specific queue:
  python -m poc_stage4_5.llm_annotate_harmful_interaction --queue PATH

  # All 42 examples:
  python -m poc_stage4_5.llm_annotate_harmful_interaction --all

  # Dry run (no writes, no API calls):
  python -m poc_stage4_5.llm_annotate_harmful_interaction --dry-run
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dotenv import load_dotenv
from openai import OpenAI

from poc_stage4_5 import common
from poc_stage4_5.annotate_harmful_interaction import ANNOTATIONS_FIELDNAMES
from poc_stage4_5.llm_annotation_prompts import (
    PROMPT_VERSION,
    COARSE_SYSTEM, COARSE_USER_TEMPLATE,
    FINE_SYSTEM, FINE_USER_TEMPLATE,
    ADJUDICATION_SYSTEM, ADJUDICATION_USER_TEMPLATE,
)

load_dotenv(_REPO_ROOT / ".env")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LLM_MODEL = "o4-mini"
LLM_PROVIDER = "openai"
LLM_MAX_TOKENS = 512
LLM_MAX_RETRIES = 3
LLM_RETRY_BASE_SECONDS = 2.0

CHUNK_SIZE_TOKENS = 512
CHUNK_OVERLAP_TOKENS = 64
FINE_WINDOW_TOKENS = 64
FINE_OVERLAP_TOKENS = 16
CONSENSUS_TOLERANCE_TOKENS = 64
NUM_INDEPENDENT_PASSES = 2

DEFAULT_PILOT_QUEUE = common.DEFAULT_REVIEW_DIR / "pilot_example_queue.csv"
DEFAULT_OUTPUT_BASE = (
    common.REPO_ROOT / "outputs" / "stage4_5" / "llm_harmful_interaction_annotations"
)

# ---------------------------------------------------------------------------
# LLM call helper
# ---------------------------------------------------------------------------

def _call_llm(
    client: OpenAI,
    system_prompt: str,
    user_prompt: str,
    logger: logging.Logger,
) -> dict | None:
    """Call o4-mini with JSON output mode. Returns parsed dict or None on failure."""
    for attempt in range(LLM_MAX_RETRIES):
        try:
            resp = client.chat.completions.create(
                model=LLM_MODEL,
                max_completion_tokens=LLM_MAX_TOKENS,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "user", "content": system_prompt + "\n\n" + user_prompt},
                ],
            )
            content = resp.choices[0].message.content or ""
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning("JSON decode error (attempt %d/%d): %s", attempt + 1, LLM_MAX_RETRIES, e)
            if attempt + 1 < LLM_MAX_RETRIES:
                time.sleep(LLM_RETRY_BASE_SECONDS * (2 ** attempt))
        except Exception as e:
            logger.warning("LLM call error (attempt %d/%d): %s", attempt + 1, LLM_MAX_RETRIES, e)
            if attempt + 1 < LLM_MAX_RETRIES:
                time.sleep(LLM_RETRY_BASE_SECONDS * (2 ** attempt))
    return None


# ---------------------------------------------------------------------------
# Coarse pass
# ---------------------------------------------------------------------------

def _build_chunks(think_tokens: list[dict]) -> list[dict]:
    """Split think-phase tokens into overlapping chunks of CHUNK_SIZE_TOKENS."""
    chunks = []
    n = len(think_tokens)
    step = max(1, CHUNK_SIZE_TOKENS - CHUNK_OVERLAP_TOKENS)
    i = 0
    while i < n:
        end = min(i + CHUNK_SIZE_TOKENS, n)
        chunk_toks = think_tokens[i:end]
        chunk_text = "".join(t.get("token_text", "") for t in chunk_toks)
        chunks.append({
            "chunk_idx": len(chunks),
            "start_tok_pos": i,
            "end_tok_pos": end,
            "chunk_start_gen_idx": chunk_toks[0]["generated_token_index"],
            "chunk_end_gen_idx": chunk_toks[-1]["generated_token_index"],
            "chunk_text": chunk_text,
            "tokens": chunk_toks,
        })
        if end == n:
            break
        i += step
    return chunks


def _run_coarse_pass(
    client: OpenAI,
    goal_index: int,
    chunks: list[dict],
    logger: logging.Logger,
) -> list[dict]:
    """Run coarse detection on all chunks. Returns list of result dicts."""
    results = []
    for chunk in chunks:
        user_prompt = COARSE_USER_TEMPLATE.format(
            goal_index=goal_index,
            chunk_start=chunk["chunk_start_gen_idx"],
            chunk_end=chunk["chunk_end_gen_idx"],
            chunk_text=chunk["chunk_text"],
        )
        raw = _call_llm(client, COARSE_SYSTEM, user_prompt, logger)
        if raw is None:
            results.append({
                "chunk_idx": chunk["chunk_idx"],
                "chunk_start_gen_idx": chunk["chunk_start_gen_idx"],
                "chunk_end_gen_idx": chunk["chunk_end_gen_idx"],
                "status": "provider_error",
                "contains_possible_onset": False,
                "earliest_possible_local_offset": None,
                "confidence": 0.0,
                "reason_category": "uncertain",
                "brief_rationale": "provider_error",
                "raw_response": None,
            })
        else:
            results.append({
                "chunk_idx": chunk["chunk_idx"],
                "chunk_start_gen_idx": chunk["chunk_start_gen_idx"],
                "chunk_end_gen_idx": chunk["chunk_end_gen_idx"],
                "status": raw.get("status", "uncertain"),
                "contains_possible_onset": bool(raw.get("contains_possible_onset", False)),
                "earliest_possible_local_offset": raw.get("earliest_possible_local_offset"),
                "confidence": float(raw.get("confidence", 0.0)),
                "reason_category": raw.get("reason_category", "uncertain"),
                "brief_rationale": str(raw.get("brief_rationale", ""))[:300],
                "raw_response": None,  # do not store full response
            })
    return results


# ---------------------------------------------------------------------------
# Fine localization pass
# ---------------------------------------------------------------------------

def _build_fine_windows(
    candidate_chunk: dict,
    think_tokens: list[dict],
) -> list[dict]:
    """Build 64-token overlapping windows around the candidate chunk."""
    # Expand context: start one chunk overlap before, end one overlap after
    all_gen_indices = {t["generated_token_index"]: i for i, t in enumerate(think_tokens)}
    start_gen = candidate_chunk["chunk_start_gen_idx"]
    end_gen = candidate_chunk["chunk_end_gen_idx"]

    # Find position in think_tokens list
    start_pos = all_gen_indices.get(start_gen, 0)
    end_pos = all_gen_indices.get(end_gen, len(think_tokens) - 1) + 1

    # Expand slightly for context
    context_start = max(0, start_pos - FINE_OVERLAP_TOKENS)
    context_end = min(len(think_tokens), end_pos + FINE_OVERLAP_TOKENS)
    region_tokens = think_tokens[context_start:context_end]

    windows = []
    step = max(1, FINE_WINDOW_TOKENS - FINE_OVERLAP_TOKENS)
    i = 0
    while i < len(region_tokens):
        end = min(i + FINE_WINDOW_TOKENS, len(region_tokens))
        win_toks = region_tokens[i:end]
        # Build character-offset map
        char_pos = 0
        tok_map: list[tuple[int, int]] = []  # (gen_token_index, char_start)
        for t in win_toks:
            tok_map.append((t["generated_token_index"], char_pos))
            char_pos += len(t.get("token_text", ""))
        window_text = "".join(t.get("token_text", "") for t in win_toks)
        # Format map as compact string (limit to avoid huge prompts)
        map_str = "; ".join(f"{idx}@{cs}" for idx, cs in tok_map[:30])
        if len(tok_map) > 30:
            map_str += f" ... ({len(tok_map) - 30} more)"
        windows.append({
            "win_idx": len(windows),
            "window_start_gen": win_toks[0]["generated_token_index"],
            "window_end_gen": win_toks[-1]["generated_token_index"],
            "window_text": window_text,
            "token_index_map": map_str,
            "tokens": win_toks,
        })
        if end == len(region_tokens):
            break
        i += step
    return windows


def _run_fine_pass(
    client: OpenAI,
    goal_index: int,
    windows: list[dict],
    logger: logging.Logger,
) -> dict | None:
    """Run fine localization on windows. Return first 'annotated' result, or best."""
    best = None
    for win in windows:
        user_prompt = FINE_USER_TEMPLATE.format(
            goal_index=goal_index,
            window_start=win["window_start_gen"],
            window_end=win["window_end_gen"],
            token_index_map=win["token_index_map"],
            window_text=win["window_text"],
        )
        raw = _call_llm(client, FINE_SYSTEM, user_prompt, logger)
        if raw is None:
            continue
        status = raw.get("annotation_status", "uncertain")
        if status == "annotated":
            result = {
                "annotation_status": "annotated",
                "onset_local_offset": raw.get("onset_local_offset"),
                "onset_generated_token_index": raw.get("onset_generated_token_index"),
                "onset_segment": raw.get("onset_segment", "think"),
                "confidence": float(raw.get("confidence", 0.0)),
                "reason_category": raw.get("reason_category", "uncertain"),
                "brief_rationale": str(raw.get("brief_rationale", ""))[:300],
                "window_start_gen": win["window_start_gen"],
                "window_end_gen": win["window_end_gen"],
            }
            if best is None:
                best = result
            elif result["onset_generated_token_index"] is not None:
                if (best.get("onset_generated_token_index") is None or
                        result["onset_generated_token_index"] < best["onset_generated_token_index"]):
                    best = result
    return best


# ---------------------------------------------------------------------------
# Token index validation
# ---------------------------------------------------------------------------

def _validate_token_index(
    index: int | None,
    tokens: list[dict],
) -> bool:
    """Check that index is a real generated_token_index in the token list."""
    if index is None:
        return False
    valid = {t["generated_token_index"] for t in tokens}
    return index in valid


def _get_token_phase(index: int, tokens: list[dict]) -> str:
    for t in tokens:
        if t["generated_token_index"] == index:
            return t.get("role_or_part", "unknown")
    return "unknown"


# ---------------------------------------------------------------------------
# Full single-example annotation (one pass)
# ---------------------------------------------------------------------------

def _annotate_single_pass(
    client: OpenAI,
    example_id: str,
    goal_index: int,
    tokens: list[dict],
    logger: logging.Logger,
) -> dict:
    """Run one full annotation pass. Returns a pass result dict."""
    think_tokens = [t for t in tokens if t.get("role_or_part") == "think"]
    if not think_tokens:
        return {
            "annotation_status": "no_harmful_interaction_found",
            "onset_generated_token_index": None,
            "onset_segment": "none",
            "confidence": 1.0,
            "reason_category": "uncertain",
            "brief_rationale": "no_think_phase_tokens",
        }

    # Coarse pass
    chunks = _build_chunks(think_tokens)
    coarse_results = _run_coarse_pass(client, goal_index, chunks, logger)
    candidates = [r for r in coarse_results if r["contains_possible_onset"]]

    if not candidates:
        return {
            "annotation_status": "no_harmful_interaction_found",
            "onset_generated_token_index": None,
            "onset_segment": "none",
            "confidence": 0.7,
            "reason_category": "uncertain",
            "brief_rationale": "no_candidate_chunk_found_in_coarse_pass",
        }

    # Take earliest candidate
    earliest_chunk = min(candidates, key=lambda r: r["chunk_start_gen_idx"])
    chunk_obj = next(c for c in chunks if c["chunk_idx"] == earliest_chunk["chunk_idx"])

    # Fine pass
    windows = _build_fine_windows(chunk_obj, think_tokens)
    fine_result = _run_fine_pass(client, goal_index, windows, logger)

    if fine_result is None or fine_result.get("annotation_status") != "annotated":
        return {
            "annotation_status": "uncertain",
            "onset_generated_token_index": None,
            "onset_segment": "none",
            "confidence": 0.3,
            "reason_category": earliest_chunk.get("reason_category", "uncertain"),
            "brief_rationale": "fine_pass_did_not_annotate",
        }

    idx = fine_result.get("onset_generated_token_index")
    if not _validate_token_index(idx, tokens):
        logger.warning("Fine pass returned invalid token index %s for %s", idx, example_id)
        # Try to snap to nearest valid index in window
        valid = {t["generated_token_index"] for t in tokens}
        window_gen_indices = [t["generated_token_index"] for t in
                              (next((w["tokens"] for w in windows
                                     if w["window_start_gen"] == fine_result.get("window_start_gen")),
                                    windows[0]["tokens"]) if windows else [])]
        valid_in_window = [i for i in window_gen_indices if i in valid]
        if valid_in_window and idx is not None:
            closest = min(valid_in_window, key=lambda i: abs(i - idx))
            idx = closest
            fine_result["onset_generated_token_index"] = idx
        else:
            return {
                "annotation_status": "uncertain",
                "onset_generated_token_index": None,
                "onset_segment": "none",
                "confidence": 0.2,
                "reason_category": "uncertain",
                "brief_rationale": "invalid_token_index_from_fine_pass",
            }

    phase = _get_token_phase(idx, tokens)
    return {
        "annotation_status": "annotated",
        "onset_generated_token_index": idx,
        "onset_segment": phase,
        "confidence": fine_result.get("confidence", 0.5),
        "reason_category": fine_result.get("reason_category", "uncertain"),
        "brief_rationale": fine_result.get("brief_rationale", ""),
    }


# ---------------------------------------------------------------------------
# Two-pass consensus + adjudication
# ---------------------------------------------------------------------------

def _run_adjudication(
    client: OpenAI,
    goal_index: int,
    idx_a: int,
    idx_b: int,
    tokens: list[dict],
    logger: logging.Logger,
) -> dict:
    """Run adjudication between two disagreeing indices."""
    lo = min(idx_a, idx_b)
    hi = max(idx_a, idx_b)
    # Build a context window covering both candidates with ±32 tokens padding
    valid_gen = sorted(t["generated_token_index"] for t in tokens)
    lo_pos = valid_gen.index(lo) if lo in valid_gen else 0
    hi_pos = valid_gen.index(hi) if hi in valid_gen else len(valid_gen) - 1
    start_pos = max(0, lo_pos - 32)
    end_pos = min(len(valid_gen), hi_pos + 32)
    window_gen = valid_gen[start_pos:end_pos]
    tok_map_toks = [t for t in tokens if t["generated_token_index"] in set(window_gen)]
    tok_map_toks.sort(key=lambda t: t["generated_token_index"])

    char_pos = 0
    map_items = []
    text_parts = []
    for t in tok_map_toks:
        map_items.append(f"{t['generated_token_index']}@{char_pos}")
        text_parts.append(t.get("token_text", ""))
        char_pos += len(t.get("token_text", ""))
    window_text = "".join(text_parts)
    map_str = "; ".join(map_items[:40])
    if len(map_items) > 40:
        map_str += f" ... ({len(map_items) - 40} more)"

    user_prompt = ADJUDICATION_USER_TEMPLATE.format(
        goal_index=goal_index,
        candidate_a=idx_a,
        candidate_b=idx_b,
        token_index_map=map_str,
        window_text=window_text,
    )
    raw = _call_llm(client, ADJUDICATION_SYSTEM, user_prompt, logger)
    if raw is None:
        return {"annotation_status": "uncertain", "onset_generated_token_index": None}

    choice = raw.get("choice", "uncertain")
    chosen = raw.get("chosen_index")
    rationale = str(raw.get("brief_rationale", ""))[:300]

    if choice == "A":
        if _validate_token_index(idx_a, tokens):
            return {"annotation_status": "annotated", "onset_generated_token_index": idx_a,
                    "brief_rationale": rationale}
    elif choice == "B":
        if _validate_token_index(idx_b, tokens):
            return {"annotation_status": "annotated", "onset_generated_token_index": idx_b,
                    "brief_rationale": rationale}
    elif choice == "new" and chosen is not None:
        if _validate_token_index(chosen, tokens):
            return {"annotation_status": "annotated", "onset_generated_token_index": chosen,
                    "brief_rationale": rationale}
    elif choice == "no_event":
        return {"annotation_status": "no_harmful_interaction_found",
                "onset_generated_token_index": None, "brief_rationale": rationale}

    return {"annotation_status": "uncertain", "onset_generated_token_index": None,
            "brief_rationale": rationale}


def _consensus(
    client: OpenAI,
    example_id: str,
    goal_index: int,
    tokens: list[dict],
    logger: logging.Logger,
) -> dict:
    """Run two independent passes and compute consensus."""
    results = []
    for pass_num in range(1, NUM_INDEPENDENT_PASSES + 1):
        r = _annotate_single_pass(client, example_id, goal_index, tokens, logger)
        r["pass_number"] = pass_num
        results.append(r)
        logger.debug("Pass %d for %s: status=%s idx=%s",
                     pass_num, example_id, r["annotation_status"],
                     r.get("onset_generated_token_index"))

    p1, p2 = results[0], results[1]
    p1_ok = p1["annotation_status"] == "annotated" and p1.get("onset_generated_token_index") is not None
    p2_ok = p2["annotation_status"] == "annotated" and p2.get("onset_generated_token_index") is not None

    if p1_ok and p2_ok:
        dist = abs(p1["onset_generated_token_index"] - p2["onset_generated_token_index"])
        if dist <= CONSENSUS_TOLERANCE_TOKENS:
            # Agreement: use earlier index
            chosen_idx = min(p1["onset_generated_token_index"],
                             p2["onset_generated_token_index"])
            phase = _get_token_phase(chosen_idx, tokens)
            mean_conf = (p1["confidence"] + p2["confidence"]) / 2
            return {
                "annotation_status": "annotated",
                "harmful_interaction_start_token": chosen_idx,
                "onset_segment": phase,
                "confidence": mean_conf,
                "reason_category": p1.get("reason_category", "uncertain"),
                "brief_rationale": p1.get("brief_rationale", ""),
                "pass_1_status": p1["annotation_status"],
                "pass_1_index": p1["onset_generated_token_index"],
                "pass_1_confidence": p1["confidence"],
                "pass_2_status": p2["annotation_status"],
                "pass_2_index": p2["onset_generated_token_index"],
                "pass_2_confidence": p2["confidence"],
                "adjudication_used": False,
                "agreement_distance_tokens": dist,
            }
        else:
            # Disagreement: adjudicate
            logger.info("Passes disagree by %d tokens for %s; adjudicating.", dist, example_id)
            adj = _run_adjudication(
                client, goal_index,
                p1["onset_generated_token_index"],
                p2["onset_generated_token_index"],
                tokens, logger,
            )
            adj_idx = adj.get("onset_generated_token_index")
            phase = _get_token_phase(adj_idx, tokens) if adj_idx is not None else "none"
            return {
                "annotation_status": adj.get("annotation_status", "uncertain"),
                "harmful_interaction_start_token": adj_idx,
                "onset_segment": phase,
                "confidence": (p1["confidence"] + p2["confidence"]) / 2 * 0.8,
                "reason_category": "uncertain",
                "brief_rationale": adj.get("brief_rationale", ""),
                "pass_1_status": p1["annotation_status"],
                "pass_1_index": p1["onset_generated_token_index"],
                "pass_1_confidence": p1["confidence"],
                "pass_2_status": p2["annotation_status"],
                "pass_2_index": p2["onset_generated_token_index"],
                "pass_2_confidence": p2["confidence"],
                "adjudication_used": True,
                "agreement_distance_tokens": dist,
            }

    # At least one pass did not produce an annotated result
    statuses = {p1["annotation_status"], p2["annotation_status"]}
    if "no_harmful_interaction_found" in statuses and "annotated" not in statuses:
        status = "no_harmful_interaction_found"
    elif "annotated" in statuses:
        # One annotated, one did not — use the annotated one with reduced confidence
        annotated_pass = p1 if p1_ok else p2
        other_pass = p2 if p1_ok else p1
        idx = annotated_pass["onset_generated_token_index"]
        phase = _get_token_phase(idx, tokens)
        return {
            "annotation_status": "uncertain",
            "harmful_interaction_start_token": idx,
            "onset_segment": phase,
            "confidence": annotated_pass["confidence"] * 0.6,
            "reason_category": annotated_pass.get("reason_category", "uncertain"),
            "brief_rationale": "one_pass_annotated_one_did_not",
            "pass_1_status": p1["annotation_status"],
            "pass_1_index": p1.get("onset_generated_token_index"),
            "pass_1_confidence": p1["confidence"],
            "pass_2_status": p2["annotation_status"],
            "pass_2_index": p2.get("onset_generated_token_index"),
            "pass_2_confidence": p2["confidence"],
            "adjudication_used": False,
            "agreement_distance_tokens": None,
        }
    else:
        status = "uncertain"

    return {
        "annotation_status": status,
        "harmful_interaction_start_token": None,
        "onset_segment": "none",
        "confidence": min(p1["confidence"], p2["confidence"]),
        "reason_category": "uncertain",
        "brief_rationale": f"passes_both_{status}",
        "pass_1_status": p1["annotation_status"],
        "pass_1_index": p1.get("onset_generated_token_index"),
        "pass_1_confidence": p1["confidence"],
        "pass_2_status": p2["annotation_status"],
        "pass_2_index": p2.get("onset_generated_token_index"),
        "pass_2_confidence": p2["confidence"],
        "adjudication_used": False,
        "agreement_distance_tokens": None,
    }


# ---------------------------------------------------------------------------
# SHA-256 of trace
# ---------------------------------------------------------------------------

def _trace_sha256(tokens: list[dict]) -> str:
    text = "".join(t.get("token_text", "") for t in tokens)
    return hashlib.sha256(text.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

CONSENSUS_CSV_FIELDS: list[str] = [
    "example_id", "goal_index", "attack_iteration", "conversation_id",
    "trace_path", "trace_sha256",
    "annotation_status",
    "harmful_interaction_start_token",
    "onset_segment",
    "confidence",
    "reason_category",
    "pass_1_status", "pass_1_index", "pass_1_confidence",
    "pass_2_status", "pass_2_index", "pass_2_confidence",
    "adjudication_used", "agreement_distance_tokens",
    "right_censored", "segmentation_complete",
    "judge_provider", "judge_model", "judge_prompt_version",
    "timestamp_utc",
]


def _make_run_dir(base: Path, timestamp: str | None = None) -> Path:
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = base / f"run_{timestamp}"
    for sub in ("logs",):
        (run_dir / sub).mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _already_annotated(example_id: str, consensus_csv: Path) -> bool:
    if not consensus_csv.exists():
        return False
    for r in common.read_csv_as_list(consensus_csv):
        if r.get("example_id") == example_id:
            return True
    return False


def _write_raw_pass(
    run_dir: Path,
    example_id: str,
    pass_number: int,
    pass_result: dict,
    meta: dict,
) -> None:
    row = {
        "example_id": example_id,
        "pass_number": pass_number,
        "annotation_status": pass_result.get("annotation_status"),
        "onset_generated_token_index": pass_result.get("onset_generated_token_index"),
        "onset_segment": pass_result.get("onset_segment"),
        "confidence": pass_result.get("confidence"),
        "reason_category": pass_result.get("reason_category"),
        "brief_rationale": pass_result.get("brief_rationale"),
        "goal_index": meta.get("goal_index"),
        "attack_iteration": meta.get("attack_iteration"),
        "conversation_id": meta.get("conversation_id"),
        "judge_model": LLM_MODEL,
        "judge_provider": LLM_PROVIDER,
        "judge_prompt_version": PROMPT_VERSION,
        "timestamp_utc": common.utc_now(),
        # Explicitly NOT storing: token_text, chunk_text, window_text (no raw trace)
    }
    common.append_jsonl(run_dir / "raw_passes.jsonl", row)


def _get_git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=common.REPO_ROOT,
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------------
# Main annotation loop
# ---------------------------------------------------------------------------

def annotate_examples(
    example_ids: list[str],
    run_dir: Path,
    dry_run: bool,
    logger: logging.Logger,
) -> None:
    import os
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not set. Cannot proceed.")
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    consensus_csv = run_dir / "consensus_annotations.csv"
    dataset = common.load_analysis_dataset()
    meta_map = {r["example_id"]: r for r in dataset}

    for eid in example_ids:
        if _already_annotated(eid, consensus_csv):
            logger.info("SKIP (already annotated): %s", eid)
            continue

        meta = meta_map.get(eid, {})
        seg_status = meta.get("thinking_segmentation_status", "")
        right_censored = meta.get("right_censored", False)

        logger.info("Annotating: %s (goal=%s, think_tokens=%s)",
                    eid, meta.get("goal_index"), meta.get("think_token_count"))

        # Load tokens
        try:
            artifact = common.load_stage4_per_example(eid)
        except FileNotFoundError:
            logger.warning("Stage4 per-example artifact not found: %s", eid)
            row = _make_error_row(eid, meta, "provider_error", "stage4_artifact_not_found")
            if not dry_run:
                common.append_csv_row(consensus_csv, row, CONSENSUS_CSV_FIELDS)
            continue

        tokens = artifact.get("token_level_data", [])
        trace_path = str(common.STAGE4_PER_EXAMPLE_DIR /
                         f"{common.example_id_to_s4_filename(eid)}.json")

        if seg_status != "parsed_from_think_tags":
            logger.info("  Not separable: %s", eid)
            row = _make_error_row(eid, meta, "no_harmful_interaction_found",
                                  "not_separable", tokens, trace_path)
            if not dry_run:
                common.append_csv_row(consensus_csv, row, CONSENSUS_CSV_FIELDS)
            continue

        if dry_run:
            logger.info("  [DRY RUN] would annotate %s", eid)
            continue

        # Run two-pass consensus
        goal_index = int(meta.get("goal_index", -1))
        result = _consensus(client, eid, goal_index, tokens, logger)

        # Build consensus row
        sha = _trace_sha256(tokens)
        row = {
            "example_id": eid,
            "goal_index": meta.get("goal_index"),
            "attack_iteration": meta.get("attack_iteration"),
            "conversation_id": meta.get("conversation_id"),
            "trace_path": trace_path,
            "trace_sha256": sha,
            "annotation_status": result.get("annotation_status", "uncertain"),
            "harmful_interaction_start_token": result.get("harmful_interaction_start_token", ""),
            "onset_segment": result.get("onset_segment", "none"),
            "confidence": result.get("confidence", 0.0),
            "reason_category": result.get("reason_category", "uncertain"),
            "pass_1_status": result.get("pass_1_status", ""),
            "pass_1_index": result.get("pass_1_index", ""),
            "pass_1_confidence": result.get("pass_1_confidence", ""),
            "pass_2_status": result.get("pass_2_status", ""),
            "pass_2_index": result.get("pass_2_index", ""),
            "pass_2_confidence": result.get("pass_2_confidence", ""),
            "adjudication_used": result.get("adjudication_used", False),
            "agreement_distance_tokens": result.get("agreement_distance_tokens", ""),
            "right_censored": right_censored,
            "segmentation_complete": seg_status == "parsed_from_think_tags",
            "judge_provider": LLM_PROVIDER,
            "judge_model": LLM_MODEL,
            "judge_prompt_version": PROMPT_VERSION,
            "timestamp_utc": common.utc_now(),
        }
        common.append_csv_row(consensus_csv, row, CONSENSUS_CSV_FIELDS)

        # Also write raw passes JSONL (no trace text)
        for pass_num in range(1, 3):
            pass_key_prefix = f"pass_{pass_num}_"
            pass_result = {
                "annotation_status": result.get(f"pass_{pass_num}_status", ""),
                "onset_generated_token_index": result.get(f"pass_{pass_num}_index"),
                "onset_segment": result.get("onset_segment"),
                "confidence": result.get(f"pass_{pass_num}_confidence", 0.0),
                "reason_category": result.get("reason_category"),
                "brief_rationale": result.get("brief_rationale", ""),
            }
            _write_raw_pass(run_dir, eid, pass_num, pass_result, meta)

        status = result.get("annotation_status")
        idx = result.get("harmful_interaction_start_token")
        logger.info("  -> status=%s idx=%s confidence=%.2f",
                    status, idx, float(result.get("confidence", 0)))

    logger.info("Annotation loop complete.")


def _make_error_row(
    eid: str,
    meta: dict,
    status: str,
    reason: str,
    tokens: list[dict] | None = None,
    trace_path: str = "",
) -> dict:
    sha = _trace_sha256(tokens) if tokens else ""
    return {
        "example_id": eid,
        "goal_index": meta.get("goal_index", ""),
        "attack_iteration": meta.get("attack_iteration", ""),
        "conversation_id": meta.get("conversation_id", ""),
        "trace_path": trace_path,
        "trace_sha256": sha,
        "annotation_status": status,
        "harmful_interaction_start_token": "",
        "onset_segment": "none",
        "confidence": 0.0,
        "reason_category": reason,
        "pass_1_status": status,
        "pass_1_index": "",
        "pass_1_confidence": "",
        "pass_2_status": status,
        "pass_2_index": "",
        "pass_2_confidence": "",
        "adjudication_used": False,
        "agreement_distance_tokens": "",
        "right_censored": meta.get("right_censored", ""),
        "segmentation_complete": meta.get("thinking_segmentation_status") == "parsed_from_think_tags",
        "judge_provider": LLM_PROVIDER,
        "judge_model": LLM_MODEL,
        "judge_prompt_version": PROMPT_VERSION,
        "timestamp_utc": common.utc_now(),
    }


def _write_manifest(run_dir: Path, example_ids: list[str], pilot_mode: bool) -> None:
    manifest = {
        "stage": "stage4_5b",
        "artifact_version": "stage4_5b_annotation_manifest_v1",
        "created_utc": common.utc_now(),
        "run_dir": str(run_dir),
        "judge_provider": LLM_PROVIDER,
        "judge_model": LLM_MODEL,
        "judge_prompt_version": PROMPT_VERSION,
        "temperature": 0,
        "max_retries": LLM_MAX_RETRIES,
        "chunk_size_tokens": CHUNK_SIZE_TOKENS,
        "chunk_overlap_tokens": CHUNK_OVERLAP_TOKENS,
        "fine_window_tokens": FINE_WINDOW_TOKENS,
        "fine_overlap_tokens": FINE_OVERLAP_TOKENS,
        "consensus_tolerance_tokens": CONSENSUS_TOLERANCE_TOKENS,
        "num_independent_passes": NUM_INDEPENDENT_PASSES,
        "n_examples": len(example_ids),
        "pilot_mode": pilot_mode,
        "git_commit": _get_git_commit(),
        "annotation_status": "automated_not_human_ground_truth",
        "contains_raw_text": False,
    }
    common.atomic_write_json(run_dir / "annotation_manifest.json", manifest)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Stage 4.5B: LLM-based harmful-interaction onset annotation.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    mode = p.add_mutually_exclusive_group()
    mode.add_argument(
        "--queue",
        type=Path,
        default=None,
        help="CSV with example_id column. Defaults to pilot queue if neither "
             "--queue nor --all is given.",
    )
    mode.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="Annotate all 42 examples (ignores quality gate).",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output run directory (auto-created with timestamp if not given).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print what would happen without making API calls or writing files.",
    )
    p.add_argument(
        "--analysis-dataset",
        type=Path,
        default=common.ANALYSIS_DATASET_PATH,
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    # Set up run directory
    if args.output_dir is not None:
        run_dir = args.output_dir
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "logs").mkdir(exist_ok=True)
    else:
        run_dir = _make_run_dir(DEFAULT_OUTPUT_BASE)

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(run_dir / "logs" / "run.log"),
        ],
    )
    logger = logging.getLogger("llm_annotate")

    # Determine example list
    if args.all:
        dataset = common.load_analysis_dataset(args.analysis_dataset)
        example_ids = [r["example_id"] for r in dataset]
        pilot_mode = False
        logger.info("Mode: ALL (%d examples)", len(example_ids))
    else:
        queue_path = args.queue if args.queue is not None else DEFAULT_PILOT_QUEUE
        if not queue_path.exists():
            logger.error("Queue file not found: %s", queue_path)
            return 1
        rows = common.read_csv_as_list(queue_path)
        example_ids = [r["example_id"] for r in rows if r.get("example_id")]
        pilot_mode = True
        logger.info("Mode: QUEUE (%d examples from %s)", len(example_ids), queue_path)

    if not example_ids:
        logger.warning("No example IDs found. Exiting.")
        return 0

    if not args.dry_run:
        _write_manifest(run_dir, example_ids, pilot_mode)

    annotate_examples(example_ids, run_dir, args.dry_run, logger)

    if not args.dry_run:
        # Write consensus JSON mirror
        consensus_csv = run_dir / "consensus_annotations.csv"
        if consensus_csv.exists():
            rows = common.read_csv_as_list(consensus_csv)
            common.atomic_write_json(
                run_dir / "consensus_annotations.json",
                {"annotations": rows, "n": len(rows)},
            )
            logger.info("Written consensus_annotations.json (%d rows)", len(rows))

    logger.info("Done. Run dir: %s", run_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
