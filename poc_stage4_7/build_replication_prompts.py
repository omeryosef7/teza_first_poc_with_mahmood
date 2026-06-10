"""
Stage 4.7 — Build multi-prompt controlled replication prompt set.

For each selected source prompt, produces 4 conditions:
  A — Original full prompt, thinking=True (baseline)
  D — Puzzle removed (target + answer cue only), thinking=True
  F — Length-matched coherent benign wrapper, thinking=True (NEW)
  E — Original full prompt, thinking=False

Condition F construction:
  - Filler text = concatenated harmless instructions from harmless_train.json
  - Filler start index = deterministic function of source_example_id hash
  - Total prompt token count within ±5% of condition A
  - Target span and answer cue preserved byte-identically
  - Filler contains no harmful-domain keywords from target span
  - Assembled as: [filler_text]\\n\\n[target_span_text]\\n\\n[answer_cue_text]

Reuses:
  - poc_stage4_6.build_controlled_ablation_prompts.identify_spans()
  - poc_stage4_6.build_controlled_ablation_prompts.build_condition()
  - poc_stage4_5.common utilities

Usage:
  python -m poc_stage4_7.build_replication_prompts [--output-dir PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage4_6.build_controlled_ablation_prompts import (
    identify_spans,
    build_condition as build_condition_46,
    _sha256_of_token_ids,
)
from poc_stage4_5 import common

_STAGE2B_JSONL = (
    _REPO_ROOT / "outputs" / "hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl"
)
_STAGE6_TRACES = _REPO_ROOT / "outputs" / "stage6" / "all_traces_full"
_HARMLESS_TRAIN = (
    _REPO_ROOT
    / "Chain_of_Thought_Hijacking"
    / "refusal_direction"
    / "dataset"
    / "splits"
    / "harmless_train.json"
)
_SOURCE_SELECTION_CSV = _REPO_ROOT / "outputs" / "stage4_7" / "source_prompt_selection.csv"
_OUTPUT_BASE = _REPO_ROOT / "outputs" / "stage4_7"

MODEL_NAME = "Qwen/Qwen3-14B"
MODEL_REVISION = "40c069824f4251a91eefaf281ebe4c544efd3e18"

CONDITIONS_4_7 = ["A", "D", "F", "E"]
LENGTH_MATCH_TOLERANCE = 0.05  # ±5%

OUTPUT_FIELDNAMES = [
    "source_example_id",
    "goal_index",
    "condition",
    "enable_thinking",
    "source_prompt_sha256",
    "transformed_prompt_sha256",
    "source_prompt_tokens",
    "transformed_prompt_tokens",
    "target_span_sha256",
    "answer_cue_sha256",
    "target_span_preserved",
    "answer_cue_preserved",
    "transformation_method",
    "benign_wrapper_source_ids",
    "benign_wrapper_sha256",
    "length_match_ratio",
    "validation_passed",
    "validation_notes",
]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _load_selection() -> list[dict]:
    rows = []
    with open(_SOURCE_SELECTION_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows


def _load_stage2b_map() -> dict[str, dict]:
    result: dict[str, dict] = {}
    with open(_STAGE2B_JSONL, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            gi = r.get("goal_index")
            ai = r.get("attack_iteration")
            ci = r.get("conversation_id")
            tm = r.get("target_model", "gpt-o4-mini")
            eid = f"goal_index={gi}|attack_iteration={ai}|conversation_id={ci}|target_model={tm}"
            result[eid] = r
    return result


def _load_harmless() -> list[str]:
    data = json.loads(_HARMLESS_TRAIN.read_text(encoding="utf-8"))
    return [item["instruction"] for item in data if item.get("instruction")]


def _load_trace(example_id: str) -> dict:
    parts = {}
    for seg in example_id.split("|"):
        k, _, v = seg.partition("=")
        parts[k] = v
    gi = parts.get("goal_index", "")
    ai = parts.get("attack_iteration", "")
    ci = parts.get("conversation_id", "")
    tm = parts.get("target_model", "gpt-o4-mini")
    fname = f"qwen3_14b_trace_goal_index_{gi}_attack_iteration_{ai}_conversation_id_{ci}_target_model_{tm}.json"
    path = _STAGE6_TRACES / fname
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Tokenizer (CPU only — for length matching)
# ---------------------------------------------------------------------------

_tokenizer_cache: dict[str, Any] = {}


def _get_tokenizer():
    if "tok" not in _tokenizer_cache:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(
            MODEL_NAME, revision=MODEL_REVISION, trust_remote_code=True
        )
        _tokenizer_cache["tok"] = tok
    return _tokenizer_cache["tok"]


def _tokenize_text(text: str) -> list[int]:
    tok = _get_tokenizer()
    return tok.encode(text, add_special_tokens=False)


# ---------------------------------------------------------------------------
# Keyword extraction for F validation
# ---------------------------------------------------------------------------

_COMMON_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "to", "of", "and", "or", "in", "on",
    "at", "by", "for", "with", "from", "as", "this", "that", "it", "its",
    "they", "them", "their", "you", "your", "we", "our", "i", "my", "me",
    "he", "she", "his", "her", "not", "but", "so", "if", "than", "then",
    "when", "where", "which", "who", "how", "what", "all", "any", "some",
}


def _extract_harmful_keywords(target_text: str, answer_text: str) -> set[str]:
    """Extract multi-character non-common words from target and answer cue."""
    combined = (target_text + " " + answer_text).lower()
    tokens = re.findall(r"[a-z]{4,}", combined)
    keywords = {t for t in tokens if t not in _COMMON_WORDS}
    return keywords


def _filler_has_harmful_keywords(filler: str, harmful_kw: set[str]) -> list[str]:
    filler_lower = filler.lower()
    found = [kw for kw in harmful_kw if kw in filler_lower]
    return found


# ---------------------------------------------------------------------------
# Condition F builder
# ---------------------------------------------------------------------------

def _deterministic_start_index(example_id: str, n_items: int) -> int:
    h = hashlib.sha256(example_id.encode()).digest()
    val = int.from_bytes(h[:4], "big")
    return val % n_items


def build_condition_f(
    example_id: str,
    span_info: dict,
    stage2_row: dict,
    harmless: list[str],
) -> dict[str, Any]:
    """
    Build condition F: coherent length-matched benign wrapper.

    Returns dict with all required fields.
    """
    notes: list[str] = []

    # Target and answer cue texts
    prompt_tokens = span_info["prompt_tokens"]
    n = span_info["n_prompt_tokens"]
    cs = span_info.get("content_start_idx", 3)
    ce = span_info.get("content_end_idx", n - 5)

    target_start, target_end = span_info["target_span"]
    acue_start, acue_end = span_info["answer_cue_span"]

    target_text = "".join(
        prompt_tokens[i]["decoded_single_token"]
        for i in range(target_start, target_end)
        if not prompt_tokens[i].get("is_special_token", False)
    )
    answer_cue_text = "".join(
        prompt_tokens[i]["decoded_single_token"]
        for i in range(acue_start, min(acue_end, n))
        if not prompt_tokens[i].get("is_special_token", False)
    )

    # Condition A token count (reference)
    tokens_a = span_info["n_prompt_tokens"]  # full prompt length
    target_count = tokens_a  # tokens in A

    # Target token count for F: match condition A
    # Condition D tokens = special + target_span + answer_cue
    d_token_ids = [
        prompt_tokens[i]["token_id"]
        for i in range(n)
        if i not in set(span_info["puzzle_indices"])
    ]
    tokens_d = len(d_token_ids)

    # Token deficit = A tokens - D tokens (the puzzle wrapper size)
    deficit = tokens_a - tokens_d

    # Extract harmful keywords to exclude from filler
    harmful_kw = _extract_harmful_keywords(target_text, answer_cue_text)

    # Deterministic start index into harmless pool
    start_idx = _deterministic_start_index(example_id, len(harmless))

    # Accumulate filler items from harmless pool (cycling)
    filler_items: list[str] = []
    filler_item_indices: list[int] = []
    filler_text = ""
    n_harmless = len(harmless)
    approx_chars_per_token = 4.0

    target_chars = int(deficit * approx_chars_per_token * 1.1)  # slight over-estimate
    idx = start_idx
    while len(filler_text) < target_chars:
        item = harmless[idx % n_harmless]
        # Skip items with harmful keywords
        bad_kw = _filler_has_harmful_keywords(item, harmful_kw)
        if bad_kw:
            idx += 1
            continue
        filler_items.append(item)
        filler_item_indices.append(idx % n_harmless)
        filler_text = "\n\n".join(filler_items)
        idx += 1
        if idx - start_idx > n_harmless * 3:
            notes.append("WARN: cycled harmless pool >3 times to find safe filler")
            break

    # Assemble F prompt text: filler + target + answer cue
    f_user_message = f"{filler_text}\n\n{target_text}\n\n{answer_cue_text}"

    # Tokenize to get actual token count via chat template
    tok = _get_tokenizer()

    def _count_with_chat_template(user_text: str, enable_thinking: bool) -> int:
        messages = [{"role": "user", "content": user_text}]
        try:
            formatted = tok.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                enable_thinking=enable_thinking,
                return_tensors=None,
            )
            return len(formatted)
        except Exception:
            # Fallback: tokenize without template
            return len(tok.encode(user_text, add_special_tokens=True))

    # Get condition A token count via tokenization (use the original user message)
    cs_idx = span_info.get("content_start_idx", 3)
    ce_idx = span_info.get("content_end_idx", n - 5)
    a_user_message = "".join(
        prompt_tokens[i]["decoded_single_token"]
        for i in range(n)
        if cs_idx <= i <= ce_idx and not prompt_tokens[i].get("is_special_token", False)
    )
    tokens_a_actual = _count_with_chat_template(a_user_message, enable_thinking=True)

    # Iteratively adjust filler to hit ±5% of tokens_a_actual
    max_iters = 20
    for iteration in range(max_iters):
        tokens_f = _count_with_chat_template(f_user_message, enable_thinking=True)
        ratio = tokens_f / tokens_a_actual if tokens_a_actual > 0 else 1.0

        if abs(ratio - 1.0) <= LENGTH_MATCH_TOLERANCE:
            break

        if ratio > 1.0 + LENGTH_MATCH_TOLERANCE:
            # Too long — remove last filler item
            if len(filler_items) > 1:
                removed = filler_items.pop()
                filler_item_indices.pop()
                filler_text = "\n\n".join(filler_items)
                f_user_message = f"{filler_text}\n\n{target_text}\n\n{answer_cue_text}"
            else:
                # Can't remove more — truncate filler text by tokens
                notes.append("WARN: single filler item too long, truncating")
                break
        else:
            # Too short — add next safe harmless item
            next_idx = (filler_item_indices[-1] + 1) % n_harmless if filler_item_indices else (start_idx + len(filler_items)) % n_harmless
            attempts = 0
            while attempts < n_harmless:
                item = harmless[next_idx % n_harmless]
                bad_kw = _filler_has_harmful_keywords(item, harmful_kw)
                if not bad_kw:
                    filler_items.append(item)
                    filler_item_indices.append(next_idx % n_harmless)
                    filler_text = "\n\n".join(filler_items)
                    f_user_message = f"{filler_text}\n\n{target_text}\n\n{answer_cue_text}"
                    break
                next_idx += 1
                attempts += 1
            else:
                notes.append("WARN: exhausted harmless pool trying to extend filler")
                break

    # Final validation
    tokens_f_final = _count_with_chat_template(f_user_message, enable_thinking=True)
    ratio_final = tokens_f_final / tokens_a_actual if tokens_a_actual > 0 else 1.0
    length_match_ok = abs(ratio_final - 1.0) <= LENGTH_MATCH_TOLERANCE

    # Check target span preserved
    target_span_preserved = target_text in f_user_message
    answer_cue_preserved = answer_cue_text.strip()[:50] in f_user_message

    # Check no harmful keywords in filler (NOT in target+answer, which are allowed)
    filler_only = filler_text
    bad_in_filler = _filler_has_harmful_keywords(filler_only, harmful_kw)

    # Compute filler SHA256
    benign_sha256 = hashlib.sha256(filler_text.encode()).hexdigest()

    # Compute F prompt SHA256 (using tokenized ids through chat template)
    try:
        messages = [{"role": "user", "content": f_user_message}]
        f_token_ids = tok.apply_chat_template(
            messages, tokenize=True, add_generation_prompt=True,
            enable_thinking=True, return_tensors=None,
        )
        f_sha256 = _sha256_of_token_ids(list(f_token_ids))
    except Exception:
        f_sha256 = hashlib.sha256(f_user_message.encode()).hexdigest()
        f_token_ids = _tokenize_text(f_user_message)

    validation_passed = True
    if not length_match_ok:
        notes.append(f"FAIL: length_match_ratio={ratio_final:.4f} outside ±5% (tokens_f={tokens_f_final}, tokens_a={tokens_a_actual})")
        validation_passed = False
    if not target_span_preserved:
        notes.append("FAIL: target span not found in F prompt text")
        validation_passed = False
    if not answer_cue_preserved:
        notes.append("WARN: answer cue may not be fully preserved (first 50 chars not found)")
    if bad_in_filler:
        notes.append(f"FAIL: harmful keywords found in benign filler: {bad_in_filler[:5]}")
        validation_passed = False

    if validation_passed and not notes:
        notes.append("OK")

    return {
        "user_message_text": f_user_message,
        "token_count": tokens_f_final,
        "token_ids": list(f_token_ids),
        "length_match_ratio": round(ratio_final, 6),
        "benign_wrapper_source_ids": filler_item_indices,
        "benign_wrapper_sha256": benign_sha256,
        "target_span_preserved": target_span_preserved,
        "answer_cue_preserved": answer_cue_preserved,
        "transformed_prompt_sha256": f_sha256,
        "validation_passed": validation_passed,
        "validation_notes": notes,
        "tokens_a_actual": tokens_a_actual,
    }


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_replication_prompts(
    output_dir: Path | None = None,
    dry_run: bool = False,
) -> list[dict]:
    out_dir = output_dir or _OUTPUT_BASE
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Loading source selection ...")
    selection = _load_selection()
    print(f"  {len(selection)} source prompts")

    print("Loading Stage 2B map ...")
    s2b_map = _load_stage2b_map()

    print("Loading harmless dataset ...")
    harmless = _load_harmless()
    print(f"  {len(harmless)} harmless instructions")

    print("Loading tokenizer (CPU) ...")
    _get_tokenizer()
    print("  tokenizer ready")

    all_rows: list[dict] = []
    all_passed = True

    for sel in selection:
        eid = sel["example_id"]
        goal_index = int(sel["goal_index"])

        print(f"\n--- {eid} (goal={goal_index}, stratum={sel['selection_stratum']}) ---")

        stage2_row = s2b_map.get(eid)
        if stage2_row is None:
            raise RuntimeError(f"No Stage 2B row for {eid}")

        trace = _load_trace(eid)
        span_info = identify_spans(trace, stage2_row)
        n_puzzle = len(span_info["puzzle_indices"])
        n_prompt = span_info["n_prompt_tokens"]
        print(f"  prompt_tokens={n_prompt} puzzle_tokens={n_puzzle}")

        if n_puzzle == 0:
            print(f"  WARN: no puzzle tokens — building conditions with 0-token puzzle")

        # --- Condition A ---
        a_result = build_condition_46("A", span_info, 1.0, __import__("random").Random(47))
        a_sha256 = span_info["full_prompt_sha256"]

        # Get actual A token count via chat template
        tok = _get_tokenizer()
        a_user_msg = a_result["user_message_text"]
        try:
            messages = [{"role": "user", "content": a_user_msg}]
            a_token_ids_full = tok.apply_chat_template(
                messages, tokenize=True, add_generation_prompt=True,
                enable_thinking=True, return_tensors=None,
            )
            a_token_count_actual = len(a_token_ids_full)
        except Exception:
            a_token_ids_full = tok.encode(a_user_msg, add_special_tokens=True)
            a_token_count_actual = len(a_token_ids_full)

        # --- Condition D ---
        d_result = build_condition_46("D", span_info, 0.0, __import__("random").Random(47))

        # --- Condition E ---
        e_result = build_condition_46("E", span_info, 1.0, __import__("random").Random(47))

        # --- Condition F ---
        f_result = build_condition_f(eid, span_info, stage2_row, harmless)

        condition_results = {
            "A": (a_result, {
                "transformation_method": "identity_copy",
                "benign_wrapper_source_ids": [],
                "benign_wrapper_sha256": "",
                "length_match_ratio": 1.0,
                "enable_thinking": True,
            }),
            "D": (d_result, {
                "transformation_method": "deletion_only_no_puzzle",
                "benign_wrapper_source_ids": [],
                "benign_wrapper_sha256": "",
                "length_match_ratio": None,
                "enable_thinking": True,
            }),
            "F": (None, f_result),
            "E": (e_result, {
                "transformation_method": "identity_copy_thinking_disabled",
                "benign_wrapper_source_ids": [],
                "benign_wrapper_sha256": "",
                "length_match_ratio": None,
                "enable_thinking": False,
            }),
        }

        for cond in CONDITIONS_4_7:
            if cond == "F":
                fr = f_result
                user_msg = fr["user_message_text"]
                tok_count = fr["token_count"]
                tok_ids = fr.get("token_ids", [])
                tf_sha256 = fr["transformed_prompt_sha256"]
                enable_thinking = True
                transformation_method = "benign_wrapper_length_matched"
                benign_ids = fr["benign_wrapper_source_ids"]
                benign_sha = fr["benign_wrapper_sha256"]
                lr = fr["length_match_ratio"]
                tgt_preserved = fr["target_span_preserved"]
                acue_preserved = fr["answer_cue_preserved"]
                v_passed = fr["validation_passed"]
                v_notes = fr["validation_notes"]
            else:
                r, meta = condition_results[cond]
                user_msg = r["user_message_text"]
                tok_count = r["prompt_token_count"]
                # compute sha256 of token ids as in stage 4.6
                tf_sha256 = r["prompt_token_ids_sha256"]
                enable_thinking = meta["enable_thinking"]
                transformation_method = meta["transformation_method"]
                benign_ids = meta["benign_wrapper_source_ids"]
                benign_sha = meta["benign_wrapper_sha256"]
                lr = meta["length_match_ratio"]
                tgt_preserved = r.get("validation_notes", [""])[0] != "FAIL: target span not fully preserved"
                acue_preserved = True
                v_passed = r["validation_passed"]
                v_notes = r["validation_notes"]

            if not v_passed:
                all_passed = False
                print(f"  FAIL cond={cond}: {v_notes}")
            else:
                print(f"  cond={cond}: tokens={tok_count} ratio={lr} passed={v_passed}")

            row: dict = {
                "source_example_id": eid,
                "goal_index": goal_index,
                "condition": cond,
                "enable_thinking": enable_thinking,
                "selection_stratum": sel.get("selection_stratum", ""),
                "source_prompt_sha256": a_sha256,
                "transformed_prompt_sha256": tf_sha256,
                "source_prompt_tokens": n_prompt,
                "transformed_prompt_tokens": tok_count,
                "target_span_sha256": span_info["target_span_sha256"],
                "answer_cue_sha256": span_info["answer_cue_span_sha256"],
                "target_span_preserved": tgt_preserved,
                "answer_cue_preserved": acue_preserved,
                "transformation_method": transformation_method,
                "benign_wrapper_source_ids": json.dumps(benign_ids),
                "benign_wrapper_sha256": benign_sha,
                "length_match_ratio": lr,
                "validation_passed": v_passed,
                "validation_notes": "; ".join(str(n) for n in v_notes),
                # Runtime fields (not in CSV fieldnames — JSONL only)
                "_goal": stage2_row.get("goal", ""),
                "_user_message_text": user_msg,
                "_enable_thinking": enable_thinking,
                "_source_example_id": eid,
            }
            all_rows.append(row)

    print(f"\n{len(all_rows)} rows built ({len(selection)} prompts × {len(CONDITIONS_4_7)} conditions)")

    if dry_run:
        print("[DRY RUN] — no files written.")
        return all_rows

    # Write JSONL (full including runtime fields)
    jsonl_path = out_dir / "replication_prompts.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for row in all_rows:
            # Exclude goal text (_goal) from file — no raw harmful text
            safe = {k: v for k, v in row.items() if k != "_goal"}
            f.write(json.dumps(safe, default=str) + "\n")
    print(f"Wrote {jsonl_path} ({len(all_rows)} rows)")

    # Write CSV (metadata only, no runtime fields)
    csv_path = out_dir / "replication_prompts_manifest.csv"
    meta_rows = [{k: v for k, v in r.items() if not k.startswith("_")} for r in all_rows]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=OUTPUT_FIELDNAMES)
        w.writeheader()
        w.writerows(meta_rows)
    print(f"Wrote {csv_path}")

    if not all_passed:
        print("\nERROR: some validation checks failed — see output above")
        sys.exit(1)

    print("\nAll replication prompts validated OK.")
    return all_rows


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build Stage 4.7 replication prompts.")
    p.add_argument("--output-dir", type=Path, default=None)
    p.add_argument("--dry-run", action="store_true", default=False)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    build_replication_prompts(output_dir=args.output_dir, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
