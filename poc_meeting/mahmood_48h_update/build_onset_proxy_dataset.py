#!/usr/bin/env python3
"""
Task 2, Step 1 — Build onset proxy dataset.

Heuristic token-overlap method: extracts the approximate first position in each
generated thinking trace where the model engages with the harmful target.

NOTE: LLM-based annotation (Stage 4.5 approach) was blocked by safety filters.
This script uses only local, non-LLM heuristics. All output is redacted.

No raw harmful target text is printed in logs or output. Sensitive terms are
replaced with [REDACTED] in the redacted_snippet column.

Usage:
    python -m poc_meeting.mahmood_48h_update.build_onset_proxy_dataset \
        --output-dir outputs/meeting/mahmood_48h_update_<TIMESTAMP>
"""

import argparse
import csv
import hashlib
import json
import logging
import re
import string
import sys
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stderr)
log = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Common English stopwords
_STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "if", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought", "used",
    "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they",
    "what", "which", "who", "whom", "whose", "when", "where", "why", "how",
    "all", "each", "every", "both", "either", "neither", "more", "most", "other",
    "some", "such", "no", "not", "only", "own", "same", "so", "than", "too",
    "very", "just", "because", "as", "until", "while", "although", "though",
    "even", "still", "yet", "also", "then", "now", "here", "there", "up",
    "about", "against", "between", "into", "through", "during", "before", "after",
    "above", "below", "out", "off", "over", "under", "again", "further", "once",
})

# Common puzzle/wrapper structural words to exclude from target keywords
_PUZZLE_STRUCTURAL = frozenset({
    "puzzle", "constraint", "constraints", "filler", "wrapper", "answer", "cue",
    "question", "solve", "solving", "solution", "problem", "task", "hint", "clue",
    "step", "steps", "first", "next", "then", "think", "thinking", "reason",
    "reasoning", "provide", "write", "explain", "describe", "example", "note",
    "given", "using", "ensure", "make", "sure", "please", "your", "my", "our",
    "their", "new", "know", "need", "want", "must", "get", "one", "two", "three",
    "four", "five", "six", "set", "here", "following", "below", "above", "like",
    "information", "see", "look", "let", "try", "help", "start", "end", "complete",
    "based", "given", "use", "also", "will", "s", "t",
})

_EXCLUDED_TERMS = _STOPWORDS | _PUZZLE_STRUCTURAL


def _tokenize(text: str) -> list[str]:
    """Simple word-level tokenizer: lowercase, strip punctuation."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return [w for w in text.split() if w and len(w) > 2]


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _extract_target_keywords_from_d_prompt(d_prompt_text: str) -> frozenset[str]:
    """
    Extract target-specific terms from a condition D (no-puzzle) prompt.
    D = bare target span + answer cue. Removing stopwords and structural words
    leaves target-domain terms.
    """
    tokens = _tokenize(d_prompt_text)
    keywords = frozenset(t for t in tokens if t not in _EXCLUDED_TERMS and len(t) > 3)
    return keywords


def _find_onset(think_tokens: list[str], target_keywords: frozenset[str],
                window: int = 20, min_matches: int = 1) -> dict:
    """
    Find the first position in think_tokens where target keywords appear.
    Uses a sliding window of `window` tokens.
    Returns onset metrics dict.
    """
    if not target_keywords or not think_tokens:
        return {"onset_token_idx": None, "onset_percent": None,
                "tokens_before_onset": None, "tokens_after_onset": None,
                "onset_bucket": "unavailable", "confidence": "unavailable",
                "matching_method": "unavailable", "match_count": 0}

    n = len(think_tokens)
    for i in range(n):
        end = min(i + window, n)
        window_tokens = think_tokens[i:end]
        matches = sum(1 for t in window_tokens if t in target_keywords)
        if matches >= min_matches:
            pct = i / n if n > 0 else 0.0
            if pct < 1/3:
                bucket = "early"
            elif pct < 2/3:
                bucket = "middle"
            else:
                bucket = "late"
            # Confidence based on match density
            density = matches / min(window, n - i)
            if density >= 0.1:
                conf = "high"
            elif density >= 0.04:
                conf = "medium"
            else:
                conf = "low"
            return {
                "onset_token_idx": i,
                "onset_percent": round(pct, 4),
                "tokens_before_onset": i,
                "tokens_after_onset": n - i,
                "onset_bucket": bucket,
                "confidence": conf,
                "matching_method": "target_overlap",
                "match_count": matches,
            }

    return {"onset_token_idx": None, "onset_percent": None,
            "tokens_before_onset": n, "tokens_after_onset": 0,
            "onset_bucket": "none", "confidence": "low",
            "matching_method": "target_overlap", "match_count": 0}


def _redacted_snippet(think_tokens: list[str], onset_idx: int | None,
                      target_keywords: frozenset[str], window: int = 25) -> str:
    """Extract a snippet around onset with sensitive terms masked."""
    if onset_idx is None or not think_tokens:
        return ""
    start = max(0, onset_idx - 10)
    end = min(len(think_tokens), onset_idx + window)
    snippet_tokens = []
    for t in think_tokens[start:end]:
        if t in target_keywords:
            snippet_tokens.append("[REDACTED]")
        else:
            snippet_tokens.append(t)
    return " ".join(snippet_tokens)


def _load_per_run_jsons_s47(run_dir: Path) -> list[dict]:
    """Load Stage 4.7 per-run JSON files."""
    runs_dir = run_dir / "runs"
    if not runs_dir.exists():
        log.warning("Stage 4.7 runs/ not found: %s", runs_dir)
        return []
    entries = []
    for f in sorted(runs_dir.glob("*.json")):
        try:
            with open(f) as fh:
                d = json.load(fh)
            entries.append(d)
        except Exception as e:
            log.warning("Failed to load %s: %s", f, e)
    return entries


def _load_per_example_jsons_s48(run_dir: Path) -> list[dict]:
    """Load Stage 4.8 per-example JSON files."""
    pe_dir = run_dir / "per_example"
    if not pe_dir.exists():
        log.warning("Stage 4.8 per_example/ not found: %s", pe_dir)
        return []
    entries = []
    for f in sorted(pe_dir.glob("*.json")):
        try:
            with open(f) as fh:
                d = json.load(fh)
            entries.append(d)
        except Exception as e:
            log.warning("Failed to load %s: %s", f, e)
    return entries


def _build_target_keyword_map(entries: list[dict]) -> dict[str, frozenset[str]]:
    """
    Build a map from source_example_id → target_keywords using condition D prompt text.
    Condition D = bare target + answer cue, so its prompt yields target-domain keywords.
    """
    kw_map: dict[str, frozenset[str]] = {}
    for e in entries:
        if e.get("condition") != "D":
            continue
        src_id = e.get("source_example_id", "")
        prompt = e.get("user_message_text", "")
        if not prompt:
            continue
        kw = _extract_target_keywords_from_d_prompt(prompt)
        # Also use answer cue sha if available to mark that we found the D prompt
        if src_id and kw:
            kw_map[src_id] = kw
    return kw_map


def _sr_success_from_entry(e: dict) -> bool | None:
    # Stage 4.7 uses sr_success (from canonical CSV) or strongreject_is_success
    # Stage 4.8 uses sr_success
    for key in ("sr_success", "strongreject_is_success", "is_success"):
        val = e.get(key)
        if val is not None:
            if isinstance(val, bool):
                return val
            return str(val).lower() == "true"
    score = e.get("strongreject_score")
    if score is not None:
        return float(score) >= 0.5
    return None


def process_entries(entries: list[dict], stage: str, kw_map: dict[str, frozenset]) -> list[dict]:
    """Process a list of per-run/per-example dicts into onset proxy rows."""
    rows = []
    for e in entries:
        src_id = e.get("source_example_id", "")
        cond = e.get("condition", "")
        goal = str(e.get("goal_index", ""))
        think_text = e.get("think_text", "")

        # Skip if thinking is disabled or no thinking text
        if not think_text or e.get("enable_thinking") is False:
            continue

        run_id = e.get("run_id", "")
        sr_success = _sr_success_from_entry(e)
        sr_score = float(e.get("strongreject_score") or 0.0)
        think_token_count = int(e.get("think_token_count") or 0)

        # Tokenize thinking text
        think_tokens = _tokenize(think_text)

        # Get target keywords
        keywords = kw_map.get(src_id, frozenset())
        if not keywords:
            onset = {"onset_token_idx": None, "onset_percent": None,
                     "tokens_before_onset": len(think_tokens), "tokens_after_onset": 0,
                     "onset_bucket": "unavailable", "confidence": "unavailable",
                     "matching_method": "unavailable", "match_count": 0}
            redacted_ctx_hash = ""
            snippet = ""
            reason_unavailable = "no_D_condition_prompt_found_for_this_source_example"
        else:
            onset = _find_onset(think_tokens, keywords)
            idx = onset.get("onset_token_idx")
            snippet = _redacted_snippet(think_tokens, idx, keywords)
            redacted_ctx_hash = _hash_text(snippet) if snippet else ""
            reason_unavailable = ""

        seed = e.get("seed", None)
        row = {
            "example_id": run_id,
            "source_example_id": src_id,
            "goal_index": goal,
            "condition": cond,
            "stage": stage,
            "seed": seed if seed is not None else "",
            "sr_success": sr_success,
            "strongreject_score": round(sr_score, 4),
            "think_token_count": think_token_count,
            "onset_token_idx": onset["onset_token_idx"],
            "onset_percent": onset["onset_percent"],
            "tokens_before_onset": onset["tokens_before_onset"],
            "tokens_after_onset": onset["tokens_after_onset"],
            "onset_bucket": onset["onset_bucket"],
            "confidence": onset["confidence"],
            "matching_method": onset["matching_method"],
            "match_count": onset["match_count"],
            "redacted_context_hash": redacted_ctx_hash,
            "redacted_snippet": snippet,
            "n_target_keywords": len(keywords),
            "reason_unavailable": reason_unavailable,
        }
        rows.append(row)
    return rows


def compute_quality_report(rows: list[dict]) -> dict:
    conf_counts = {}
    method_counts = {}
    n_unavailable = 0
    for r in rows:
        conf = r["confidence"]
        conf_counts[conf] = conf_counts.get(conf, 0) + 1
        m = r["matching_method"]
        method_counts[m] = method_counts.get(m, 0) + 1
        if r["onset_bucket"] == "unavailable":
            n_unavailable += 1

    n = len(rows)
    n_high_med = conf_counts.get("high", 0) + conf_counts.get("medium", 0)
    return {
        "total_examples": n,
        "confidence_counts": conf_counts,
        "method_counts": method_counts,
        "n_unavailable": n_unavailable,
        "unavailable_rate": round(n_unavailable / n, 4) if n > 0 else 0.0,
        "n_high_medium_confidence": n_high_med,
        "high_medium_confidence_rate": round(n_high_med / n, 4) if n > 0 else 0.0,
        "onset_bucket_counts": {
            b: sum(1 for r in rows if r["onset_bucket"] == b)
            for b in ("early", "middle", "late", "none", "unavailable")
        },
        "note": (
            "Onset proxy is heuristic (token-overlap). "
            "Use high+medium confidence rows only for analysis. "
            "See manual_onset_review_packet.csv for validation."
        ),
    }


FIELDNAMES = [
    "example_id", "source_example_id", "goal_index", "condition", "stage", "seed",
    "sr_success", "strongreject_score", "think_token_count",
    "onset_token_idx", "onset_percent", "tokens_before_onset", "tokens_after_onset",
    "onset_bucket", "confidence", "matching_method", "match_count",
    "redacted_context_hash", "redacted_snippet", "n_target_keywords", "reason_unavailable",
]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--s47-dir", type=Path,
                        default=_REPO_ROOT / "outputs/stage4_7/runs/run_array_20260610_1442")
    parser.add_argument("--s48-dir", type=Path,
                        default=_REPO_ROOT / "outputs/stage4_8/runs/run_array_20260611_0109")
    args = parser.parse_args(argv)

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # ── Stage 4.7 ──────────────────────────────────────────────────────────
    log.info("Loading Stage 4.7 per-run JSONs from %s", args.s47_dir)
    s47_entries = _load_per_run_jsons_s47(args.s47_dir)
    log.info("  Loaded %d entries", len(s47_entries))

    kw_map_47 = _build_target_keyword_map(s47_entries)
    log.info("  Built target keyword map: %d source example IDs with D condition", len(kw_map_47))
    if kw_map_47:
        sample_id = next(iter(kw_map_47))
        kw_sample = kw_map_47[sample_id]
        log.info("  Sample: %s → %d keywords (not logging terms)", sample_id, len(kw_sample))

    rows_47 = process_entries(s47_entries, "4.7", kw_map_47)
    log.info("  Processed %d onset rows for Stage 4.7", len(rows_47))

    # ── Stage 4.8 ──────────────────────────────────────────────────────────
    log.info("Loading Stage 4.8 per-example JSONs from %s", args.s48_dir)
    s48_entries = _load_per_example_jsons_s48(args.s48_dir)
    log.info("  Loaded %d entries", len(s48_entries))

    kw_map_48 = _build_target_keyword_map(s48_entries)
    log.info("  Built target keyword map for Stage 4.8: %d source example IDs", len(kw_map_48))

    rows_48 = process_entries(s48_entries, "4.8", kw_map_48)
    log.info("  Processed %d onset rows for Stage 4.8", len(rows_48))

    all_rows = rows_47 + rows_48
    log.info("Total onset rows: %d", len(all_rows))

    # Write onset_proxy_dataset.csv
    dataset_path = out / "onset_proxy_dataset.csv"
    with open(dataset_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        w.writeheader()
        w.writerows(all_rows)
    log.info("Wrote %s (%d rows)", dataset_path, len(all_rows))

    # Write quality report
    qr = compute_quality_report(all_rows)
    qr_path = out / "onset_quality_report.json"
    qr_path.write_text(json.dumps(qr, indent=2))
    log.info("Wrote %s", qr_path)
    log.info("Quality: %d/%d high+medium confidence (%.1f%%)",
             qr["n_high_medium_confidence"], qr["total_examples"],
             100 * qr["high_medium_confidence_rate"])
    log.info("Unavailable: %d (%.1f%%)", qr["n_unavailable"], 100 * qr["unavailable_rate"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
