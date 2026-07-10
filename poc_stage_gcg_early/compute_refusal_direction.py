"""
Compute the refusal direction vector v_refusal for a model.

v_refusal = normalize(mean(h_harmful) - mean(h_harmless))
  at `layer_idx`, last input token position.

Based on: CoT Hijacking paper (Zhao et al. 2026), Section 4.
Ablating v_refusal at layer 25 raises Qwen3-14B ASR from 11% → 91%.
We compute this vector so GCG can minimize the dot product of adversarial
suffix activations against it (see --lambda-refusal-dir in run_optimization.py).

Usage:
  python -m poc_stage_gcg_early.compute_refusal_direction \\
      --model-family qwen3 \\
      --manifest outputs/stage_gcg_full/advbench_manifest_v1.jsonl \\
      --layer 25 \\
      --output outputs/stage_gcg_full/refusal_direction_qwen3_L25.pt
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

import torch
import torch.nn.functional as F

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# 20 harmless questions used as the negative class for v_refusal
_HARMLESS_INSTRUCTIONS = [
    "What is photosynthesis and how does it work?",
    "Write a short poem about autumn leaves.",
    "Explain the water cycle in simple terms.",
    "What are the main ingredients in chocolate cake?",
    "How do I care for a houseplant?",
    "What is the capital of France?",
    "Describe the life cycle of a butterfly.",
    "How does a rainbow form?",
    "Write a haiku about mountains.",
    "What are some healthy breakfast ideas?",
    "Explain how a compass works.",
    "What is the boiling point of water?",
    "Describe the main characters in Romeo and Juliet.",
    "How do I tie a bowline knot?",
    "What is the difference between a simile and a metaphor?",
    "Explain the concept of supply and demand.",
    "What are the planets in our solar system?",
    "How do I make a paper airplane?",
    "What is the speed of light?",
    "Describe how volcanoes form.",
]


def _extract_last_token_hs(
    model, tokenizer, model_family: str, enable_thinking: bool,
    instruction: str, neutral_suffix: str, layer_idx: int, device
) -> torch.Tensor:
    """Forward pass with neutral suffix, extract hidden state at last input token, specified layer."""
    from poc_stage_gcg_early.model_adapter import apply_chat_template, tokenize_continuation, tokenize_prompt

    formatted = apply_chat_template(tokenizer, instruction, model_family, enable_thinking, add_generation_prompt=True)
    prefix_ids = tokenize_prompt(tokenizer, formatted)
    suffix_ids = tokenize_continuation(tokenizer, neutral_suffix)
    full_ids = prefix_ids + suffix_ids

    input_ids = torch.tensor(full_ids, dtype=torch.long).unsqueeze(0).to(device)
    with torch.no_grad():
        out = model(input_ids=input_ids, output_hidden_states=True)

    if layer_idx >= len(out.hidden_states):
        raise ValueError(f"Model only has {len(out.hidden_states)} hidden state layers, requested {layer_idx}")

    # Last token of the input sequence (last suffix token)
    last_pos = input_ids.shape[1] - 1
    h = out.hidden_states[layer_idx][0, last_pos, :]  # [d_model]
    return h.float().cpu()


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute refusal direction vector v_refusal")
    parser.add_argument("--model-family", default="qwen3", choices=["qwen3", "gemma4"])
    parser.add_argument("--model-name-or-path", default=None,
                        help="HF model id (default: Qwen/Qwen3-14B for qwen3, google/gemma-4-E4B-it for gemma4)")
    parser.add_argument("--manifest", type=Path,
                        default=_REPO_ROOT / "outputs/stage_gcg_full/advbench_manifest_v1.jsonl",
                        help="Path to advbench manifest (for harmful instructions)")
    parser.add_argument("--layer", type=int, default=25,
                        help="Layer index to extract activations from (default: 25, per CoT Hijacking paper)")
    parser.add_argument("--neutral-suffix", default=" ",
                        help="Neutral suffix string (default: single space)")
    parser.add_argument("--output", type=Path,
                        default=None,
                        help="Output path for v_refusal .pt file")
    parser.add_argument("--no-thinking", action="store_true")
    args = parser.parse_args()

    model_name = args.model_name_or_path or (
        "Qwen/Qwen3-14B" if args.model_family == "qwen3" else "google/gemma-4-E4B-it"
    )
    output_path = args.output or (
        _REPO_ROOT / f"outputs/stage_gcg_full/refusal_direction_{args.model_family}_L{args.layer}.pt"
    )
    enable_thinking = not args.no_thinking

    print(f"[compute_refusal_dir] model={model_name}, layer={args.layer}", flush=True)
    print(f"[compute_refusal_dir] output={output_path}", flush=True)

    # Load model
    import os
    os.environ.setdefault("HF_HOME", str(_REPO_ROOT / ".cache/huggingface"))
    os.environ.setdefault("HF_HUB_CACHE", str(_REPO_ROOT / ".cache/huggingface/hub"))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[compute_refusal_dir] device={device}", flush=True)

    if args.model_family == "qwen3":
        from poc_stage4.qwen3_model import load_qwen3_model
        wrapped = load_qwen3_model(model_name, require_cuda=True, log_device_placement=True)
    else:
        from poc_stage4.qwen3_model import load_gemma4_model
        wrapped = load_gemma4_model(model_name, require_cuda=True, log_device_placement=True)

    model = wrapped.model
    tokenizer = wrapped.tokenizer
    model.eval()

    # Load harmful instructions from manifest
    manifest_rows = [json.loads(l) for l in args.manifest.read_text().splitlines() if l.strip()]
    harmful_instructions = [r["instruction"] for r in manifest_rows if r.get("split") == "train"][:20]
    print(f"[compute_refusal_dir] Using {len(harmful_instructions)} harmful instructions", flush=True)
    print(f"[compute_refusal_dir] Using {len(_HARMLESS_INSTRUCTIONS)} harmless instructions", flush=True)

    harmful_hs: List[torch.Tensor] = []
    harmless_hs: List[torch.Tensor] = []

    print("[compute_refusal_dir] Extracting harmful activations...", flush=True)
    for i, instr in enumerate(harmful_instructions):
        h = _extract_last_token_hs(
            model, tokenizer, args.model_family, enable_thinking,
            instr, args.neutral_suffix, args.layer, device
        )
        harmful_hs.append(h)
        if (i + 1) % 5 == 0:
            print(f"  {i+1}/{len(harmful_instructions)} harmful done", flush=True)

    print("[compute_refusal_dir] Extracting harmless activations...", flush=True)
    for i, instr in enumerate(_HARMLESS_INSTRUCTIONS):
        h = _extract_last_token_hs(
            model, tokenizer, args.model_family, enable_thinking,
            instr, args.neutral_suffix, args.layer, device
        )
        harmless_hs.append(h)
        if (i + 1) % 5 == 0:
            print(f"  {i+1}/{len(_HARMLESS_INSTRUCTIONS)} harmless done", flush=True)

    # Compute v_refusal
    harmful_mean = torch.stack(harmful_hs).mean(dim=0)   # [d_model]
    harmless_mean = torch.stack(harmless_hs).mean(dim=0)  # [d_model]
    v_refusal = F.normalize(harmful_mean - harmless_mean, dim=0)  # [d_model], unit vector

    proj_harmful = torch.stack([torch.dot(h / (h.norm() + 1e-8), v_refusal) for h in harmful_hs])
    proj_harmless = torch.stack([torch.dot(h / (h.norm() + 1e-8), v_refusal) for h in harmless_hs])
    print(f"\n[compute_refusal_dir] v_refusal computed (d_model={v_refusal.shape[0]})", flush=True)
    print(f"  Projection onto v_refusal — harmful:  {proj_harmful.mean():.4f} ± {proj_harmful.std():.4f}", flush=True)
    print(f"  Projection onto v_refusal — harmless: {proj_harmless.mean():.4f} ± {proj_harmless.std():.4f}", flush=True)
    print(f"  Separation (harmful - harmless mean): {(proj_harmful.mean() - proj_harmless.mean()):.4f}", flush=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(v_refusal, output_path)
    print(f"\n[compute_refusal_dir] Saved v_refusal to {output_path}", flush=True)

    # Save metadata
    import json as _json
    meta = {
        "model_family": args.model_family,
        "model_name_or_path": model_name,
        "layer": args.layer,
        "enable_thinking": enable_thinking,
        "neutral_suffix": args.neutral_suffix,
        "n_harmful": len(harmful_hs),
        "n_harmless": len(harmless_hs),
        "d_model": int(v_refusal.shape[0]),
        "proj_harmful_mean": float(proj_harmful.mean()),
        "proj_harmless_mean": float(proj_harmless.mean()),
        "separation": float(proj_harmful.mean() - proj_harmless.mean()),
    }
    meta_path = output_path.with_suffix(".json")
    meta_path.write_text(_json.dumps(meta, indent=2))
    print(f"[compute_refusal_dir] Saved metadata to {meta_path}", flush=True)


if __name__ == "__main__":
    main()
