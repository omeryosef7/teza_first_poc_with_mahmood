"""
Hook-based selected hidden-state capture.

Thin wrapper over poc_stage_ae.replay_hidden_states hook infrastructure.
Adds:
  - Selective layer capture (only requested layers, skipping unneeded ones)
  - Gradient-preserving mode for candidate activations (preserve_grad=True)
  - Detach-only mode for reference activations (preserve_grad=False)

The final LayerNorm/RMSNorm is always applied via _find_final_norm_module,
matching HF's output_hidden_states=True convention exactly. This was verified
by the Stage AE --verify-equivalence smoke test.

Return layout:
  {layer_idx: {token_pos: Tensor[d_model]}}
  layer_idx 0 = embedding output (pre-layer-0 residual stream)
  layer_idx i = post-layer-(i-1) residual stream
  layer_idx n_layers = post-final-norm residual stream (== output_hidden_states[-1])

When preserve_grad=True: tensors are on the model's device, in the model's
  compute dtype — suitable for backward().
When preserve_grad=False: tensors are CPU, fp16, detached — same as replay output.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _import_replay_utils():
    """Import hook utilities from Stage AE replay_hidden_states."""
    from poc_stage_ae.replay_hidden_states import (
        _find_final_norm_module,
        _register_layer_hooks,
    )
    return _find_final_norm_module, _register_layer_hooks


def capture_selected_states(
    model: Any,
    input_ids: torch.Tensor,
    layers: List[int],
    positions: List[int],
    *,
    preserve_grad: bool = False,
) -> Dict[int, Dict[int, torch.Tensor]]:
    """
    Run one forward pass and extract hidden states at specific (layer, position) pairs.

    Args:
        model:         loaded causal LM (Qwen3Model or raw HF model)
        input_ids:     [seq_len] or [1, seq_len] long tensor
        layers:        list of layer indices to capture (0 = embedding, n = final norm)
        positions:     list of absolute token positions to extract
        preserve_grad: if True, do NOT detach — tensors stay on device in compute dtype
                       for backward(). If False, detach + fp16 + CPU (replay convention).

    Returns:
        {layer_idx: {token_pos: Tensor[d_model]}}

    Raises:
        ValueError if a requested position is out of range for the sequence length.
        RuntimeError if the final norm module cannot be located.
    """
    _find_final_norm_module, _register_layer_hooks = _import_replay_utils()

    if input_ids.dim() == 1:
        input_ids_2d = input_ids.unsqueeze(0)
    else:
        input_ids_2d = input_ids
    seq_len = input_ids_2d.shape[1]

    for pos in positions:
        if pos < 0 or pos >= seq_len:
            raise ValueError(
                f"Requested position {pos} is out of range for sequence length {seq_len}."
            )

    device = next(model.parameters()).device

    # NOTE: _register_layer_hooks always detaches tensors to CPU fp16 regardless of
    # preserve_grad. For Stage 3 (task-only) this is fine because we never need
    # gradients through repr_loss. For Stage 6+ repr-loss gradient computation, use
    # output_hidden_states=True with inputs_embeds (see gcg_optimizer._token_gradients)
    # rather than this function — the hook path can't propagate gradients.
    handles, captured_raw, n_layers, norm_module = _register_layer_hooks(
        model, model_family=""
    )

    try:
        if preserve_grad:
            model(input_ids=input_ids_2d.to(device), use_cache=False)
        else:
            with torch.inference_mode():
                model(input_ids=input_ids_2d.to(device), use_cache=False)

        # Apply final norm to the last captured entry (matches HF output_hidden_states[-1])
        try:
            norm_dtype = next(norm_module.parameters()).dtype
        except StopIteration:
            norm_dtype = next(model.parameters()).dtype

        raw_final = captured_raw[n_layers]  # CPU fp16 tensor [seq_len, d_model]
        if preserve_grad:
            raw_final_device = raw_final.to(device=device, dtype=norm_dtype)
            normed_final = norm_module(raw_final_device.unsqueeze(0))[0]
            captured_raw[n_layers] = normed_final
        else:
            raw_final_device = raw_final.to(device=device, dtype=norm_dtype)
            normed_final = norm_module(raw_final_device.unsqueeze(0))[0]
            captured_raw[n_layers] = normed_final.detach().to(dtype=torch.float16, device="cpu")

    finally:
        for h in handles:
            h.remove()

    # Extract only the requested layers and positions
    result: Dict[int, Dict[int, torch.Tensor]] = {}
    for layer_idx in layers:
        if layer_idx not in captured_raw:
            raise ValueError(
                f"Layer {layer_idx} not in captured hidden states "
                f"(valid range: 0..{n_layers})."
            )
        layer_tensor = captured_raw[layer_idx]  # [seq_len, d_model] or on device
        result[layer_idx] = {}
        for pos in positions:
            if preserve_grad:
                result[layer_idx][pos] = layer_tensor[pos]  # stays on device with grad
            else:
                result[layer_idx][pos] = layer_tensor[pos].clone()  # CPU fp16

    if torch.cuda.is_available() and not preserve_grad:
        torch.cuda.empty_cache()

    return result


def capture_states_equivalence_check(
    model: Any,
    input_ids: torch.Tensor,
    layers: List[int],
    positions: List[int],
    atol: float = 1e-2,
) -> Dict[str, Any]:
    """
    Verify that capture_selected_states matches output_hidden_states=True.

    Runs both paths and compares tensors with torch.allclose (bf16 tolerance).
    Returns a dict with 'passed' (bool) and 'mismatches' (list of problem descriptions).
    Used in test_state_capture.py equivalence tests.
    """
    if input_ids.dim() == 1:
        input_ids_2d = input_ids.unsqueeze(0)
    else:
        input_ids_2d = input_ids

    device = next(model.parameters()).device

    # Reference path: output_hidden_states=True
    with torch.inference_mode():
        out = model(
            input_ids=input_ids_2d.to(device),
            use_cache=False,
            output_hidden_states=True,
        )
    reference_hs = [
        hs[0].detach().to(dtype=torch.float16, device="cpu")
        for hs in out.hidden_states
    ]  # list of [seq_len, d_model]

    # Hook path
    hook_result = capture_selected_states(
        model, input_ids, layers, positions, preserve_grad=False
    )

    mismatches = []
    for layer_idx in layers:
        ref_layer = reference_hs[layer_idx]  # [seq_len, d_model]
        for pos in positions:
            ref_vec = ref_layer[pos]
            hook_vec = hook_result[layer_idx][pos]
            if not torch.allclose(ref_vec.float(), hook_vec.float(), atol=atol):
                max_diff = (ref_vec.float() - hook_vec.float()).abs().max().item()
                mismatches.append(
                    f"Layer {layer_idx}, position {pos}: max_diff={max_diff:.6f} > atol={atol}"
                )

    return {
        "passed": len(mismatches) == 0,
        "mismatches": mismatches,
        "n_layers_checked": len(layers),
        "n_positions_checked": len(positions),
    }
