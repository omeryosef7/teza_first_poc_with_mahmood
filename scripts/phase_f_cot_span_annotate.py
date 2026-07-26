#!/usr/bin/env python3
"""Phase F1.1 - CoT-Hijacking prompt SPAN annotator (CPU / tokenizer-only).

Given an EXISTING attacked JSONL (schema produced by the Chain_of_Thought_Hijacking
runs: fields `goal`, `attack_prompt`, `target_response`, `target_model`, ...) and a
model name, this script reconstructs the exact string that is fed to the target model
via its own chat template and marks, for every attack example, both CHARACTER spans
and TOKEN-INDEX spans for the following components of the CoT-Hijacking prompt:

  (a) harmful_instruction        - the verbatim harmful goal, where present
  (b) benign_puzzle_scaffold     - the neutral puzzle / math framing
  (c) injected_reasoning         - the operation/tactic mapping block that ties the
                                   benign puzzle to the harmful operations
  (d) final_answer_cue           - the "solve step by step ... practical example" directive
  (e) system_prompt              - the target system prompt (if supplied / template-injected)
  (f) chat_template_tokens       - the structural special tokens added by apply_chat_template
  (g) assistant_generation_marker- the generation-prompt marker (add_generation_prompt=True)

It is fully DETERMINISTIC and reusable. No model weights are loaded; only the
tokenizer (AutoTokenizer) is used, and only to (1) apply the chat template and
(2) obtain character<->token offset mappings.

Usage:
  TROPT/.venv/bin/python scripts/phase_f_cot_span_annotate.py \
      --input outputs/phase5_qwen3_cot/phase4_cot_hf_Qwen_Qwen3-14B_dev25.jsonl \
      --model Qwen/Qwen3-14B \
      --output outputs/phase_f_cot_spans/Qwen_Qwen3-14B_spans.jsonl

The within-content locators and the char->token mapper are pure functions (no
transformers dependency) so they can be unit-tested offline; see
tests/test_cot_span_annotate.py.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from typing import Dict, List, Optional, Tuple

Span = Tuple[int, int]  # (char_start, char_end) half-open

# ---------------------------------------------------------------------------
# Pure, tokenizer-independent locators (unit-testable without transformers)
# ---------------------------------------------------------------------------

# Ordered anchors marking where the "solve-and-produce-the-answer" directive begins.
_FINAL_CUE_PATTERNS = [
    r"Requirement:",
    r"Required Output",
    r"Solve the given problem step by step",
    r"Solve the following (?:problem|complex|advanced|logic|\d)",
    r"After presenting the (?:complete|final)",
    r"After providing the solution",
    r"present a detailed practical example",
    r"detailed practical example",
    r"practical example",
]

# Anchors that open the harmful operation / tactic mapping block ("injected reasoning").
_MAPPING_PATTERNS = [
    r"Covert Action Mapping",
    r"Tactic-Function Mapping",
    r"Action Mapping",
    r"System Interaction Protocol",
    r"SIP\s+Mapping",
    r"\bpsi\(k\)\s*=",
    r"ψ\(k\)\s*=",  # psi(k) =
    r"maps? (?:Sudoku solutions|the .*?) to operations",
    r"correspond(?:s)? to the following",
    r"map(?:ping)? .*? to the corresponding",
    r"Define action set",
]

# Section-header anchors used to bound the injected-reasoning block on the right.
_SECTION_HEADER_RE = re.compile(
    r"(?m)^\s*(?:I{1,3}V?|IV|V?I{0,3}|Part\s+[IVX]+|Operational Constraints|"
    r"Formal Problem|Resource Semiring|Required Output|Requirement:)\b")

# Anchors marking the start of the benign puzzle scaffold (usually char 0).
_SCAFFOLD_PATTERNS = [
    r"^Let\s",
    r"\bSudoku\b",
    r"\bSkyscrapers\b",
    r"\blogic grid\b",
    r"\bDispersal Matrix\b",
    r"\bSolve the following\b",
    r"\bpuzzle\b",
    r"\bgrid\b",
    r"\bgraph\b",
    r"\bcategory\b",
]


def _first_match(patterns: List[str], text: str) -> Optional[Span]:
    """Return the (start,end) of the earliest match across the ordered patterns.

    Patterns are tried in order; the earliest *character position* wins, ties broken
    by pattern order. Case-insensitive, multiline.
    """
    best: Optional[Tuple[int, int, int]] = None  # (start, end, order)
    for order, pat in enumerate(patterns):
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m:
            cand = (m.start(), m.end(), order)
            if best is None or (cand[0], cand[2]) < (best[0], best[2]):
                best = cand
    if best is None:
        return None
    return best[0], best[1]


def locate_final_answer_cue(content: str) -> Optional[Span]:
    m = _first_match(_FINAL_CUE_PATTERNS, content)
    if m is None:
        return None
    return (m[0], len(content))


def locate_scaffold_start(content: str) -> int:
    m = _first_match(_SCAFFOLD_PATTERNS, content)
    return m[0] if m is not None else 0


def locate_benign_puzzle_scaffold(content: str, cue: Optional[Span]) -> Optional[Span]:
    start = locate_scaffold_start(content)
    end = cue[0] if cue is not None else len(content)
    if end <= start:
        return None
    return (start, end)


def locate_injected_reasoning(content: str, cue: Optional[Span]) -> Optional[Span]:
    m = _first_match(_MAPPING_PATTERNS, content)
    if m is None:
        return None
    start = m[0]
    right_bound = cue[0] if cue is not None else len(content)
    # bound on the right by the next section header strictly after the anchor line
    end = right_bound
    for hm in _SECTION_HEADER_RE.finditer(content):
        if hm.start() > m[1] and hm.start() < right_bound:
            end = hm.start()
            break
    if end <= start:
        return None
    return (start, end)


def locate_harmful_instruction(content: str, goal: str) -> List[Span]:
    """Verbatim (case-insensitive) occurrences of the harmful goal in the prompt."""
    if not goal:
        return []
    spans: List[Span] = []
    low_c = content.lower()
    low_g = goal.lower().strip()
    if not low_g:
        return []
    start = 0
    while True:
        idx = low_c.find(low_g, start)
        if idx == -1:
            break
        spans.append((idx, idx + len(low_g)))
        start = idx + len(low_g)
    return spans


def char_span_to_token_indices(
    offsets: List[Tuple[int, int]], cs: int, ce: int
) -> Optional[Tuple[int, int]]:
    """Map a half-open char span [cs,ce) to a half-open token-index span [ts,te).

    `offsets` is the offset_mapping from a fast tokenizer (one (start,end) per token).
    Tokens whose char interval intersects [cs,ce) are included. Zero-width offset
    entries (a==b) are ignored. Returns None if no token overlaps.
    """
    hit = [i for i, (a, b) in enumerate(offsets) if b > a and a < ce and b > cs]
    if not hit:
        return None
    return (min(hit), max(hit) + 1)


def common_prefix_len(a: str, b: str) -> int:
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


# ---------------------------------------------------------------------------
# Tokenizer-backed template layer
# ---------------------------------------------------------------------------

def find_special_token_spans(templated: str, special_tokens: List[str]) -> List[Span]:
    """Locate every occurrence of any special/added token string in `templated`."""
    toks = sorted({t for t in special_tokens if t}, key=len, reverse=True)
    if not toks:
        return []
    pat = re.compile("|".join(re.escape(t) for t in toks))
    return [(m.start(), m.end()) for m in pat.finditer(templated)]


def build_annotation(tok, content: str, goal: str, system: Optional[str]) -> Dict:
    """Produce the full per-example span record for one attack prompt."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": content})

    templated = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    templated_nogen = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)

    enc = tok(templated, return_offsets_mapping=True, add_special_tokens=False)
    offsets = [tuple(o) for o in enc["offset_mapping"]]
    n_tokens = len(enc["input_ids"])

    def to_record(spans: List[Span], located: bool) -> Dict:
        inst = []
        for (cs, ce) in spans:
            tk = char_span_to_token_indices(offsets, cs, ce)
            inst.append({
                "char_start": cs,
                "char_end": ce,
                "tok_start": tk[0] if tk else None,
                "tok_end": tk[1] if tk else None,
                "preview": (templated[cs:ce][:120] + ("..." if ce - cs > 120 else "")),
            })
        return {"located": located and bool(inst), "instances": inst}

    # locate the user content inside the templated string
    c_start = templated.find(content)
    if c_start == -1:
        raise RuntimeError("user content not found verbatim inside templated string")
    c_end = c_start + len(content)

    # ---- within-content spans (offset into templated by c_start) ----
    cue = locate_final_answer_cue(content)
    scaffold = locate_benign_puzzle_scaffold(content, cue)
    injected = locate_injected_reasoning(content, cue)
    harmful = locate_harmful_instruction(content, goal)

    def shift(sp: Optional[Span]) -> List[Span]:
        return [(c_start + sp[0], c_start + sp[1])] if sp else []

    def shift_all(sps: List[Span]) -> List[Span]:
        return [(c_start + a, c_start + b) for (a, b) in sps]

    result: Dict[str, Dict] = {}
    result["harmful_instruction"] = to_record(shift_all(harmful), bool(harmful))
    result["benign_puzzle_scaffold"] = to_record(shift(scaffold), scaffold is not None)
    result["injected_reasoning"] = to_record(shift(injected), injected is not None)
    result["final_answer_cue"] = to_record(shift(cue), cue is not None)

    # ---- system prompt ----
    sys_spans: List[Span] = []
    if system:
        s_start = templated.find(system)
        if s_start != -1:
            sys_spans.append((s_start, s_start + len(system)))
    result["system_prompt"] = to_record(sys_spans, bool(sys_spans))

    # ---- chat-template structural special tokens ----
    specials = list(getattr(tok, "all_special_tokens", []) or [])
    try:
        specials += list(tok.get_added_vocab().keys())
    except Exception:
        pass
    sp_spans = find_special_token_spans(templated, specials)
    result["chat_template_tokens"] = to_record(sp_spans, bool(sp_spans))

    # ---- generation marker (diff of gen vs nogen templated) ----
    split = common_prefix_len(templated, templated_nogen)
    # snap the split back to the start of any special token it lands inside, so the
    # marker span begins on a clean token boundary (e.g. Phi '<|assistant|>')
    for (a, b) in sp_spans:
        if a < split < b:
            split = a
            break
    gen_spans = [(split, len(templated))] if split < len(templated) else []
    result["assistant_generation_marker"] = to_record(gen_spans, bool(gen_spans))

    coverage_misses = [k for k, v in result.items() if not v["located"]]

    return {
        "content_char_len": len(content),
        "templated_char_len": len(templated),
        "n_tokens": n_tokens,
        "content_char_span": [c_start, c_end],
        "spans": result,
        "coverage_misses": coverage_misses,
    }


def slugify_model(name: str) -> str:
    return name.replace("/", "_").replace(":", "_")


def main() -> None:
    ap = argparse.ArgumentParser(description="Phase F1.1 CoT-Hijacking span annotator")
    ap.add_argument("--input", required=True, help="attacked JSONL")
    ap.add_argument("--model", required=True, help="HF model name for AutoTokenizer (tokenizer-only)")
    ap.add_argument("--output", required=True, help="output spans JSONL")
    ap.add_argument("--system-prompt", default=None, help="optional target system prompt to include+annotate")
    ap.add_argument("--limit", type=int, default=None, help="only process first N examples")
    args = ap.parse_args()

    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(args.model)
    if not tok.is_fast:
        raise RuntimeError(f"{args.model} tokenizer is not 'fast'; offset mapping unavailable")

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)

    n_in = n_out = 0
    per_cat_miss: Dict[str, int] = {}
    with open(args.input) as fin, open(args.output, "w") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            n_in += 1
            if args.limit is not None and n_out >= args.limit:
                break
            rec = json.loads(line)
            content = rec.get("attack_prompt", "")
            goal = rec.get("goal", "")
            if not content:
                continue
            ann = build_annotation(tok, content, goal, args.system_prompt)
            out = {
                "goal_index": rec.get("goal_index"),
                "task_id": rec.get("task_id"),
                "conversation_id": rec.get("conversation_id"),
                "attack_iteration": rec.get("attack_iteration"),
                "goal": goal,
                "target_model": rec.get("target_model"),
                "tokenizer": args.model,
                "is_success": rec.get("is_success"),
                "judge_score": rec.get("judge_score"),
                **ann,
            }
            fout.write(json.dumps(out, ensure_ascii=False) + "\n")
            n_out += 1
            for c in ann["coverage_misses"]:
                per_cat_miss[c] = per_cat_miss.get(c, 0) + 1

    print(f"[phase_f] input={args.input}")
    print(f"[phase_f] model(tokenizer)={args.model}")
    print(f"[phase_f] annotated {n_out} examples -> {args.output}")
    if per_cat_miss:
        print("[phase_f] per-category coverage MISSES (n examples where span not located):")
        for c, n in sorted(per_cat_miss.items(), key=lambda x: -x[1]):
            print(f"           {c}: {n}/{n_out}")
    else:
        print("[phase_f] all categories located in all examples")


if __name__ == "__main__":
    main()
