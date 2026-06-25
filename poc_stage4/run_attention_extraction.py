"""Stage 4C: Attention Pattern Extraction (P5a).

For each pure_cot_hijack example, runs a single forward pass on the full
token sequence and extracts per-head attention statistics at selected
query positions (last K thinking tokens + last K answer tokens).

Rather than storing full O(seq²) attention matrices, this script computes:
  - Per-head attention entropy at selected query positions
  - Per-head attention mass on token categories:
      puzzle_wrapper, harmful_goal, thinking, answer, other

Token categories are parsed from the Stage 6 trace `token_table` which
maps each token to its `role_or_part`.

Memory strategy: registers a hook on each attention module to capture
(batch, heads, q_len, k_len) attention weights and immediately compute
statistics before discarding. Requires disabling Flash/SDPA attention
(which doesn't return attention weights) — model is loaded with
`attn_implementation='eager'`.

RAM estimate (Qwen3-14B, eager, seq_len=12000):
  - Weights: ~28 GB (bfloat16)
  - Attention hook buffer: 1 layer at a time: 1 × 40 × K × 12000 × 4B ≈ 0.5GB (K=50)
  - Total: ~30 GB → fits on L40S 46 GB

Usage (smoke — 3 examples):
    SMOKE=1 python -m poc_stage4.run_attention_extraction

Usage (full, all 11 pure_cot_hijack):
    python -m poc_stage4.run_attention_extraction

SLURM:
    sbatch slurm_scripts/stage4_attention_extraction.slurm
"""
from __future__ import annotations

import argparse
import json
import math
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

import torch

_REPO_ROOT = Path(__file__).parent.parent
_DEFAULT_OUT_DIR = _REPO_ROOT / "outputs" / "stage4" / "attention_analysis"

_MODEL_CONFIGS = {
    "qwen3": {
        "model_name": "Qwen/Qwen3-14B",
        "revision": "40c069824f4251a91eefaf281ebe4c544efd3e18",
        "n_layers": 40,
        "n_heads": 40,
        "mech_model_family": "qwen3",
        "think_start": "<think>",
        "think_end": "</think>",
        "max_seq_len": 12000,
        "layers_to_analyze": [3, 10, 20, 26, 32, 36, 39],
    },
    "gemma4": {
        "model_name": "google/gemma-4-E4B-it",
        "n_layers": 46,
        "n_heads": 16,
        "mech_model_family": "gemma4",
        "think_start": "<start_of_turn>",
        "think_end": "<end_of_turn>",
        "max_seq_len": 10000,
        "layers_to_analyze": [3, 10, 17, 24, 35, 45],
    },
}

_N_QUERY_POSITIONS = 50  # Sample last N thinking tokens as query positions


def _entropy(attn_row: torch.Tensor) -> float:
    """Shannon entropy of a probability distribution."""
    p = attn_row.float().clamp(min=1e-9)
    return -float((p * p.log()).sum())


def _load_trace(source_id: str, model_key: str) -> Optional[dict]:
    suffix = source_id.replace("|", "_").replace("=", "_") + ".json"
    stage6 = _REPO_ROOT / "outputs" / "stage6"
    candidates = [
        stage6 / "all_traces_full_1_11" / (f"qwen3_14b_trace_{suffix}"),
        stage6 / "all_traces_full_1_11" / (f"gemma4_e4b_it_trace_{suffix}"),
        stage6 / "all_traces_full" / (f"qwen3_14b_trace_{suffix}"),
        stage6 / "gemma_traces_full_1_11_eos_fixed" / (f"gemma_4_e4b_it_trace_{suffix}"),
    ]
    for p in candidates:
        if p.exists():
            return json.loads(p.read_text())
    return None


def _find_goal_token_range(prompt_token_strings: list[str], goal_text: str) -> tuple[int, int]:
    """Find the start/end token indices where goal_text appears in the prompt tokens.

    Returns (start, end) or (-1, -1) if not found.
    Strategy: reconstruct text from token strings and match the goal substring.
    """
    if not goal_text or not prompt_token_strings:
        return -1, -1

    # Reconstruct text from token strings (Ġ = space prefix in BPE)
    decoded = [t.replace("Ġ", " ").replace("Ċ", "\n") for t in prompt_token_strings]
    cumulative = []
    pos = 0
    for tok in decoded:
        cumulative.append(pos)
        pos += len(tok)
    full_text = "".join(decoded)

    goal_lower = goal_text.lower()
    text_lower = full_text.lower()
    start_char = text_lower.find(goal_lower)
    if start_char == -1:
        # Try partial match on first 10 words
        words = goal_text.split()[:10]
        partial = " ".join(words).lower()
        start_char = text_lower.find(partial)
    if start_char == -1:
        return -1, -1

    end_char = start_char + len(goal_lower)

    # Find token indices
    start_tok = -1
    end_tok = -1
    for i, char_pos in enumerate(cumulative):
        if start_tok == -1 and char_pos >= start_char:
            start_tok = max(0, i - 1)
        if char_pos >= end_char:
            end_tok = i
            break
    if end_tok == -1:
        end_tok = len(cumulative) - 1

    return max(0, start_tok), min(len(cumulative) - 1, end_tok)


def _categorize_tokens(token_table: list[dict],
                        goal_token_range: tuple[int, int] = (-1, -1)) -> list[str]:
    """Map each token to a category: puzzle_wrapper, harmful_goal, thinking, answer, other."""
    goal_start, goal_end = goal_token_range
    categories = []
    for i, t in enumerate(token_table):
        seg = t.get("segment", "")
        role = t.get("role_or_part", "")
        if seg == "generation" and role == "thinking":
            categories.append("thinking")
        elif seg == "generation" and role == "answer":
            categories.append("answer")
        elif seg == "prompt" and role == "user":
            if goal_start >= 0 and goal_start <= i <= goal_end:
                categories.append("harmful_goal")
            else:
                categories.append("puzzle_wrapper")
        elif seg == "prompt" and role == "system":
            categories.append("system")
        else:
            categories.append("other")
    return categories


def _get_layer_module(model, layer_idx: int):
    for path in ("model.layers", "language_model.layers", "model.language_model.layers", "layers"):
        obj = model
        try:
            for part in path.split("."):
                obj = getattr(obj, part)
            return obj[layer_idx]
        except (AttributeError, TypeError, IndexError):
            continue
    raise RuntimeError(f"Cannot find transformer layers in {type(model).__name__}")


def _get_attention_module(layer_module):
    """Get the self-attention sub-module from a layer."""
    for attr in ("self_attn", "attention", "attn", "self_attention"):
        m = getattr(layer_module, attr, None)
        if m is not None:
            return m
    return layer_module


@contextmanager
def capture_attention(model, layer_indices: list[int], query_positions: list[int],
                      category_list: list[str], stats: dict):
    """Context manager that registers hooks to capture attention stats."""
    handles = []
    category_tensor = None

    def make_hook(layer_idx: int):
        def hook(module, inp, out):
            nonlocal category_tensor
            # out is typically (hidden_states, attn_weights, past_kv) or just hidden_states
            attn_w = None
            if isinstance(out, tuple):
                for o in out:
                    if isinstance(o, torch.Tensor) and o.ndim == 4:
                        # shape: (batch, heads, q_len, k_len)
                        attn_w = o
                        break
            if attn_w is None:
                return

            attn_w = attn_w.detach().float()  # (1, n_heads, q_len, k_len)
            batch, n_heads, q_len, k_len = attn_w.shape
            if batch != 1:
                return

            # Build category tensor if not done yet
            if category_tensor is None or category_tensor.shape[0] != k_len:
                unique_cats = sorted(set(category_list[:k_len]))
                cat_map = {c: i for i, c in enumerate(unique_cats)}
                cat_idx = torch.tensor([cat_map.get(category_list[i], 0)
                                        for i in range(min(k_len, len(category_list)))],
                                       dtype=torch.long, device="cpu")
                stats["_cat_map"] = cat_map
                stats["_cat_idx"] = cat_idx

            cat_idx = stats["_cat_idx"][:k_len]
            cat_map = stats["_cat_map"]
            n_cats = len(cat_map)

            layer_stats = []
            # Sample query positions (last N thinking tokens, intersected with valid q_len)
            valid_qpos = [p for p in query_positions if p < q_len]
            if not valid_qpos:
                # Fallback: last 10 positions
                valid_qpos = list(range(max(0, q_len - 10), q_len))

            for h in range(n_heads):
                head_entropies = []
                head_cat_mass = {c: [] for c in cat_map}
                for qi in valid_qpos:
                    row = attn_w[0, h, qi, :]  # (k_len,)
                    head_entropies.append(_entropy(row))
                    # Category mass
                    for c, ci in cat_map.items():
                        mask = (cat_idx == ci)
                        head_cat_mass[c].append(float(row[mask].sum()))

                layer_stats.append({
                    "head": h,
                    "mean_entropy": float(sum(head_entropies) / max(len(head_entropies), 1)),
                    "cat_mass": {c: float(sum(v) / max(len(v), 1)) for c, v in head_cat_mass.items()},
                })
            stats[f"layer_{layer_idx}"] = layer_stats

        return hook

    try:
        for li in layer_indices:
            try:
                layer = _get_layer_module(model, li)
                attn_mod = _get_attention_module(layer)
                h = attn_mod.register_forward_hook(make_hook(li))
                handles.append(h)
            except Exception as e:
                print(f"  WARNING: could not hook layer {li}: {e}")
        yield stats
    finally:
        for h in handles:
            h.remove()


def analyze_example(model, tokenizer, trace: dict, source_id: str, cfg: dict, device: torch.device) -> dict:
    """Run a single forward pass on the PROMPT ONLY and extract attention statistics.

    We analyze attention patterns during prompt encoding (not generation) since:
    - Full traces can be 13-30K tokens (OOM with eager attention)
    - Prompt tokens are 800-1500 tokens (feasible with eager attention)
    - The puzzle wrapper's representational effect is established at prompt encoding time
    """
    # Use prompt-only token IDs — never the full trace (too long for eager attention)
    token_ids = trace.get("prompt_token_ids", [])
    if not token_ids:
        return {"skipped": True, "reason": "no_prompt_token_ids"}

    # Token table for the prompt segment only
    full_table = trace.get("token_table", [])
    prompt_table = [t for t in full_table if t.get("segment", "") == "prompt"]
    # Align lengths (some traces may differ by 1 from BOS handling)
    n = min(len(token_ids), len(prompt_table)) if prompt_table else len(token_ids)
    token_ids = token_ids[:n]
    token_table = prompt_table[:n] if prompt_table else []

    max_len = cfg["max_seq_len"]
    if len(token_ids) > max_len:
        print(f"  Skipping (prompt_len={len(token_ids)} > {max_len})")
        return {"skipped": True, "seq_len": len(token_ids), "reason": "too_long"}

    seq_len = len(token_ids)

    # Find goal token range for fine-grained categorization (puzzle_wrapper vs harmful_goal)
    goal_text = (trace.get("selected_example", {})
                     .get("raw_source_row", {})
                     .get("goal", ""))
    prompt_token_strings = trace.get("prompt_token_strings", [])[:seq_len]
    goal_range = _find_goal_token_range(prompt_token_strings, goal_text)
    if goal_range[0] >= 0:
        print(f"  Goal tokens: {goal_range[0]}–{goal_range[1]} of {seq_len} "
              f"('{goal_text[:50]}')")

    categories = _categorize_tokens(token_table[:seq_len], goal_token_range=goal_range)

    # For prompt-only analysis: use the last N user tokens as query positions
    # These are the tokens at the end of the user message (closest to generation trigger)
    user_positions = [i for i, c in enumerate(categories)
                      if c in ("puzzle_wrapper", "harmful_goal", "user_prompt")]
    if user_positions:
        # Query the last N user tokens (closest to the generation trigger)
        query_positions = user_positions[-_N_QUERY_POSITIONS:]
    else:
        query_positions = list(range(max(0, seq_len - _N_QUERY_POSITIONS), seq_len))

    thinking_positions: list[int] = []  # empty for prompt-only analysis

    print(f"  prompt_len={seq_len}, n_query_pos={len(query_positions)}")

    input_ids = torch.tensor([token_ids], dtype=torch.long, device=device)
    stats: dict = {"source_example_id": source_id, "seq_len": seq_len,
                   "n_query_positions": len(query_positions),
                   "query_positions": query_positions,
                   "token_categories_summary": {c: categories.count(c) for c in set(categories)}}

    layers_to_analyze = cfg.get("layers_to_analyze", list(range(0, cfg["n_layers"], 6)))

    with torch.no_grad():
        with capture_attention(model, layers_to_analyze, query_positions, categories, stats):
            _ = model(input_ids=input_ids, output_attentions=True, use_cache=False)

    # Clean up internal keys
    stats.pop("_cat_map", None)
    stats.pop("_cat_idx", None)

    return stats


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="qwen3", choices=["qwen3", "gemma4"])
    ap.add_argument("--output-dir", default=str(_DEFAULT_OUT_DIR))
    ap.add_argument("--n-examples", type=int, default=None,
                    help="Max examples to process (smoke: 3)")
    ap.add_argument("--max-seq-len", type=int, default=None)
    args = ap.parse_args()

    import os
    smoke = int(os.environ.get("SMOKE", "0"))
    n_examples = args.n_examples or (3 if smoke else None)

    cfg = _MODEL_CONFIGS[args.model]
    if args.max_seq_len:
        cfg["max_seq_len"] = args.max_seq_len

    out_dir = Path(args.output_dir)
    per_ex_dir = out_dir / "per_example"
    per_ex_dir.mkdir(parents=True, exist_ok=True)

    # Load examples
    mech_path = _REPO_ROOT / "outputs" / "stage4" / "mechanism_classification.jsonl"
    examples = [
        json.loads(l) for l in mech_path.read_text().strip().split("\n")
        if json.loads(l).get("model_family") == cfg["mech_model_family"]
        and json.loads(l).get("mechanism") == "pure_cot_hijack"
    ]
    if n_examples:
        examples = examples[:n_examples]

    print(f"=== Attention Extraction (model={args.model}, n={len(examples)}) ===")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    # Load model with eager attention (to get attention weights back)
    from transformers import AutoModelForCausalLM, AutoTokenizer
    hf_name = cfg["model_name"]
    revision = cfg.get("revision")
    cache_dir = str(_REPO_ROOT / ".cache" / "huggingface")

    print(f"Loading {hf_name} (attn_implementation=eager) ...")
    model = AutoModelForCausalLM.from_pretrained(
        hf_name,
        revision=revision,
        cache_dir=cache_dir,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        attn_implementation="eager",
    )
    model.eval()
    tokenizer = AutoTokenizer.from_pretrained(hf_name, revision=revision, cache_dir=cache_dir)
    print("  Model loaded")

    results = []
    for i, ex in enumerate(examples):
        source_id = ex["source_example_id"]
        print(f"\n=== Example {i+1}/{len(examples)}: {source_id[:60]} ===")

        out_file = per_ex_dir / f"{source_id.replace('|', '_').replace('=', '_')}.json"
        if out_file.exists():
            print("  Already done, skipping")
            results.append(json.loads(out_file.read_text()))
            continue

        trace = _load_trace(source_id, args.model)
        if trace is None:
            print(f"  WARNING: trace not found for {source_id}")
            continue

        t0 = time.time()
        try:
            stats = analyze_example(model, tokenizer, trace, source_id, cfg, device)
        except torch.cuda.OutOfMemoryError:
            print(f"  OOM — skipping (seq too long for available VRAM)")
            stats = {"skipped": True, "reason": "OOM", "source_example_id": source_id}
        except Exception as e:
            print(f"  ERROR: {e}")
            stats = {"skipped": True, "reason": str(e), "source_example_id": source_id}

        stats["elapsed_s"] = round(time.time() - t0, 1)
        out_file.write_text(json.dumps(stats, indent=2))
        print(f"  Written: {out_file.name} ({stats['elapsed_s']:.0f}s)")
        results.append(stats)

    # Write summary
    summary = {
        "model": args.model,
        "n_examples": len(results),
        "n_skipped": sum(1 for r in results if r.get("skipped")),
        "layers_analyzed": cfg.get("layers_to_analyze"),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nDone. Written: {out_dir}/summary.json")


if __name__ == "__main__":
    main()
