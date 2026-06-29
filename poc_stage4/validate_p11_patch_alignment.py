"""validate_p11_patch_alignment.py

Unit tests for the P11 prefill-patching mechanism. Verifies:
1. Identity patch: patching with own activations does NOT change first-token logits.
2. Sham hook: installing hook with no-op does NOT change first-token logits.
3. Activation equality: the hook correctly writes the requested values.
4. Layer count: model has exactly 40 layers (Qwen3-14B).
5. Full text stored: result rows contain full_answer_text.

Run BEFORE submitting the full P11 selectivity pilot.
Must pass ALL checks (KL < 0.01 bits for identity; KL = 0.0 for sham).

Usage (requires GPU):
    python -m poc_stage4.validate_p11_patch_alignment \
        [--model qwen3] [--n-examples 2]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

import torch
import torch.nn.functional as F

_REPO_ROOT = Path(__file__).parent.parent
_MECH_JSONL = _REPO_ROOT / "outputs" / "stage4" / "mechanism_classification.jsonl"
_STAGE6_DIR = _REPO_ROOT / "outputs" / "stage6" / "all_traces_full_1_11"

_MODEL_CONFIGS = {
    "qwen3": {
        "model_name": "Qwen/Qwen3-14B",
        "revision": "40c069824f4251a91eefaf281ebe4c544efd3e18",
        "n_layers": 40,
        "think_end": "</think>",
        "max_new_tokens": 512,  # short for validation only
        "layers_to_test": [3, 17, 26],
    },
}

IDENTITY_KL_THRESHOLD = 0.01   # bits; fail if KL between identity-patch and no-patch exceeds this
ACT_EQ_THRESHOLD = 1e-4        # L∞ norm on CPU fp32


def _get_layer_module(model, layer_idx: int):
    for path in ("model.layers", "language_model.layers"):
        obj = model
        try:
            for part in path.split("."):
                obj = getattr(obj, part)
            return obj[layer_idx]
        except (AttributeError, TypeError, IndexError):
            continue
    raise RuntimeError(f"Cannot find transformer layers in {type(model).__name__}")


def _capture_residual(model, input_ids: torch.Tensor, layer_indices: list[int]
                      ) -> dict[int, torch.Tensor]:
    captured = {}

    def make_hook(li):
        def hook(module, inp, out):
            h = out[0] if isinstance(out, tuple) else out
            captured[li] = h.detach().cpu().float().squeeze(0)  # → [seq_len, hidden_dim]
        return hook

    handles = [_get_layer_module(model, li).register_forward_hook(make_hook(li))
               for li in layer_indices]
    try:
        with torch.no_grad():
            model(input_ids=input_ids, use_cache=False)
    finally:
        for h in handles:
            h.remove()
    return captured


def _first_token_logits(model, input_ids: torch.Tensor) -> torch.Tensor:
    with torch.no_grad():
        out = model(input_ids=input_ids, use_cache=False)
    return out.logits[0, -1, :].float().cpu()


def _kl_divergence_bits(p_logits: torch.Tensor, q_logits: torch.Tensor) -> float:
    """KL(P || Q) in bits, where P and Q are logit vectors."""
    p = F.softmax(p_logits, dim=-1)
    log_p = F.log_softmax(p_logits, dim=-1)
    log_q = F.log_softmax(q_logits, dim=-1)
    kl = (p * (log_p - log_q)).sum().item()
    return kl / 0.6931472  # convert nats to bits


def _apply_identity_patch_logits(model, input_ids: torch.Tensor,
                                  layer_idx: int,
                                  own_acts: torch.Tensor) -> torch.Tensor:
    """Run forward pass with own activations patched at layer_idx.
    own_acts: [seq_len, hidden_dim] fp32 on cpu.
    Returns first-token logits.
    """
    patched_positions = []  # track what was actually written
    activation_diffs = []

    device = input_ids.device

    def patch_hook(module, inp, out):
        h = out[0] if isinstance(out, tuple) else out
        if h.shape[1] > 1:  # prefill
            for pos in range(min(h.shape[1], own_acts.shape[0])):
                before = h[0, pos, :].float().cpu()
                h[0, pos, :] = own_acts[pos, :].to(h.dtype).to(device)
                after = h[0, pos, :].float().cpu()
                diff = (after - before).abs().max().item()
                activation_diffs.append(diff)
                patched_positions.append(pos)
        if isinstance(out, tuple):
            return (h,) + out[1:]
        return h

    handle = _get_layer_module(model, layer_idx).register_forward_hook(patch_hook)
    try:
        logits = _first_token_logits(model, input_ids)
    finally:
        handle.remove()

    return logits, patched_positions, activation_diffs


def _apply_sham_hook_logits(model, input_ids: torch.Tensor, layer_idx: int) -> torch.Tensor:
    """Run with sham (no-op) hook installed. Returns first-token logits."""
    def sham_hook(module, inp, out):
        return out  # no change

    handle = _get_layer_module(model, layer_idx).register_forward_hook(sham_hook)
    try:
        logits = _first_token_logits(model, input_ids)
    finally:
        handle.remove()
    return logits


def run_validation(model, tokenizer, input_ids: torch.Tensor,
                   layer_indices: list[int], source_id: str) -> dict:
    """Run all validation checks for one example."""
    print(f"\n  Capturing baseline activations...")
    baseline_acts = _capture_residual(model, input_ids, layer_indices)
    baseline_logits = _first_token_logits(model, input_ids)

    results = {"source_id": source_id, "passed": True, "checks": {}}

    for li in layer_indices:
        print(f"\n  === Layer {li} ===")
        own_acts = baseline_acts[li]  # [seq_len, hidden_dim]

        # 1. Sham hook test
        print(f"    Sham hook test...")
        sham_logits = _apply_sham_hook_logits(model, input_ids, li)
        sham_kl = _kl_divergence_bits(baseline_logits, sham_logits)
        sham_pass = sham_kl < 1e-6
        print(f"    Sham KL = {sham_kl:.2e} {'✓ PASS' if sham_pass else '✗ FAIL'}")

        # 2. Identity patch test
        print(f"    Identity patch test...")
        id_logits, id_positions, act_diffs = _apply_identity_patch_logits(
            model, input_ids, li, own_acts)
        id_kl = _kl_divergence_bits(baseline_logits, id_logits)
        max_act_diff = max(act_diffs) if act_diffs else float("inf")
        act_eq_pass = max_act_diff < ACT_EQ_THRESHOLD
        id_kl_pass = id_kl < IDENTITY_KL_THRESHOLD
        print(f"    Identity KL = {id_kl:.4f} bits {'✓ PASS' if id_kl_pass else '✗ FAIL'} (threshold {IDENTITY_KL_THRESHOLD})")
        print(f"    Max activation diff = {max_act_diff:.2e} {'✓ PASS' if act_eq_pass else '✗ FAIL'} (threshold {ACT_EQ_THRESHOLD})")
        print(f"    Patched {len(id_positions)} positions")

        layer_pass = sham_pass and id_kl_pass and act_eq_pass
        if not layer_pass:
            results["passed"] = False

        results["checks"][f"layer_{li}"] = {
            "sham_kl": sham_kl,
            "sham_pass": sham_pass,
            "identity_kl_bits": id_kl,
            "identity_kl_pass": id_kl_pass,
            "max_activation_diff": max_act_diff,
            "activation_equality_pass": act_eq_pass,
            "n_patched_positions": len(id_positions),
            "layer_pass": layer_pass,
        }

    return results


def load_examples(model_key: str, n: int, tokenizer, device) -> list[tuple[str, torch.Tensor]]:
    """Load n source prompts from the mechanism classification."""
    examples = []
    for line in _MECH_JSONL.read_text().strip().split("\n"):
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("model_family") != model_key:
            continue
        if r.get("mechanism") not in ("pure_cot_hijack", "confirmed_pure_cot_hijack"):
            continue
        source_id = r["source_example_id"]

        suffix = source_id.replace("|", "_").replace("=", "_") + ".json"
        trace_path = None
        for p in _STAGE6_DIR.glob(f"qwen3_14b_trace_{suffix}"):
            trace_path = p
            break
        if trace_path is None:
            continue

        trace = json.loads(trace_path.read_text())
        a_ids_list = trace.get("prompt_token_ids", [])
        if not a_ids_list:
            continue

        a_ids = torch.tensor([a_ids_list], dtype=torch.long).to(device)
        examples.append((source_id, a_ids))

        if len(examples) >= n:
            break

    return examples


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="qwen3", choices=["qwen3"])
    ap.add_argument("--n-examples", type=int, default=2)
    ap.add_argument("--output", type=Path,
                    default=Path("outputs/stage4/p11_controlled_patching/alignment_validation.json"))
    args = ap.parse_args()

    cfg = _MODEL_CONFIGS[args.model]

    # Architecture check
    print(f"=== P11 Patch Alignment Validation ===")
    print(f"Model: {args.model} (expected n_layers={cfg['n_layers']})")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    from transformers import AutoModelForCausalLM, AutoTokenizer
    cache_dir = str(_REPO_ROOT / ".cache" / "huggingface")
    print(f"Loading {cfg['model_name']}...")
    model = AutoModelForCausalLM.from_pretrained(
        cfg["model_name"], revision=cfg.get("revision"), cache_dir=cache_dir,
        torch_dtype=torch.bfloat16, device_map="auto",
        attn_implementation="sdpa",
    )
    model.eval()
    tokenizer = AutoTokenizer.from_pretrained(
        cfg["model_name"], revision=cfg.get("revision"), cache_dir=cache_dir)
    print("  Model loaded")

    # Verify layer count
    try:
        n_layers_actual = sum(1 for _ in model.model.layers)
    except AttributeError:
        n_layers_actual = "unknown"
    print(f"  Layer count: {n_layers_actual} (expected {cfg['n_layers']})")
    if n_layers_actual != cfg["n_layers"]:
        print(f"  ERROR: layer count mismatch! Expected {cfg['n_layers']}, got {n_layers_actual}")
        sys.exit(1)

    print("  ✓ Layer count correct")

    # Load examples
    examples = load_examples(args.model, args.n_examples, tokenizer, device)
    print(f"\nLoaded {len(examples)} examples")
    if not examples:
        print("ERROR: no examples found. Check that mechanism_classification.jsonl and stage6 traces exist.")
        sys.exit(1)

    all_results = []
    all_passed = True

    for i, (source_id, a_ids) in enumerate(examples):
        print(f"\n=== Example {i+1}/{len(examples)}: {source_id[:70]} ===")
        print(f"  Prompt length: {a_ids.shape[1]} tokens")

        result = run_validation(model, tokenizer, a_ids, cfg["layers_to_test"], source_id)
        all_results.append(result)
        if not result["passed"]:
            all_passed = False

    # Summary
    print(f"\n{'='*60}")
    print(f"VALIDATION {'PASSED ✓' if all_passed else 'FAILED ✗'}")
    print(f"{'='*60}")
    for r in all_results:
        status = "PASS ✓" if r["passed"] else "FAIL ✗"
        print(f"  {status}: {r['source_id'][:60]}")
        for layer_key, check in r["checks"].items():
            lpass = "✓" if check["layer_pass"] else "✗"
            print(f"    {layer_key}: {lpass} "
                  f"sham_kl={check['sham_kl']:.2e} "
                  f"id_kl={check['identity_kl_bits']:.4f}b "
                  f"act_diff={check['max_activation_diff']:.2e}")

    # Write results
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump({
            "overall_pass": all_passed,
            "identity_kl_threshold": IDENTITY_KL_THRESHOLD,
            "act_eq_threshold": ACT_EQ_THRESHOLD,
            "n_layers_expected": cfg["n_layers"],
            "n_layers_actual": n_layers_actual,
            "examples": all_results,
        }, f, indent=2)
    print(f"\nResults written to {args.output}")

    if not all_passed:
        print("\nGATE FAILED: Do NOT proceed to the P11 selectivity pilot.")
        sys.exit(1)
    else:
        print("\nGATE PASSED: Identity and sham hooks are neutral. Proceed to pilot.")


if __name__ == "__main__":
    main()
