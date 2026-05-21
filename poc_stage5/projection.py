from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


SUPPORTED_TOKEN_REGIONS = frozenset(
    {
        "all",
        "first_32",
        "last_32",
        "last_16",
        "last_8",
        "final_token",
    }
)


@dataclass(frozen=True)
class ProjectionRequest:
    layers: str | None
    token_regions: str | None
    max_length: int | None


@dataclass(frozen=True)
class ProjectionConfig:
    """Configuration for reusable hidden-state projection helpers."""

    max_length: int
    layers: Optional[list[int]]
    token_regions: list[str]
    include_prompt_plus_response: bool


def describe_projection_request(request: ProjectionRequest) -> dict[str, object]:
    """Describe planned projection settings without running model inference."""

    return {
        "layers": request.layers,
        "token_regions": request.token_regions,
        "max_length": request.max_length,
        "status": "skeleton_only_no_projection_computed",
    }


def _resolve_device(device: str | None) -> str:
    import torch

    if device is None or device == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError(f"Requested device {device!r}, but CUDA is not available.")
    return device


def _resolve_torch_dtype(dtype: str | None) -> Any:
    if dtype is None or dtype == "auto":
        return None

    import torch

    normalized = dtype.removeprefix("torch.")
    if not hasattr(torch, normalized):
        raise ValueError(
            f"Unknown torch dtype {dtype!r}. Expected values such as "
            "'float32', 'float16', or 'bfloat16'."
        )
    resolved = getattr(torch, normalized)
    if not isinstance(resolved, torch.dtype):
        raise ValueError(f"torch.{normalized} is not a torch dtype.")
    return resolved


def _model_input_device(model: Any) -> Any:
    try:
        embedding = model.get_input_embeddings()
        return embedding.weight.device
    except Exception:
        try:
            return next(model.parameters()).device
        except StopIteration as exc:
            raise RuntimeError("Unable to infer model device from parameters or embeddings.") from exc


def load_hf_model_and_tokenizer(
    model_name_or_path: str,
    device: str | None = "auto",
    dtype: str | None = "auto",
) -> tuple[Any, Any]:
    """Load a local/open-source HuggingFace causal LM and tokenizer.

    `device="auto"` selects CUDA when available, otherwise CPU. `dtype="auto"`
    leaves dtype selection to HuggingFace/model defaults and is never passed to
    tensor `.to(dtype=...)`.
    """

    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise RuntimeError(
            "Loading HuggingFace models requires transformers in the active Python environment."
        ) from exc

    resolved_device = _resolve_device(device)
    torch_dtype = _resolve_torch_dtype(dtype)
    model_kwargs: dict[str, Any] = {}
    if torch_dtype is not None:
        model_kwargs["torch_dtype"] = torch_dtype

    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
    model = AutoModelForCausalLM.from_pretrained(model_name_or_path, **model_kwargs)
    model.to(resolved_device)
    model.eval()
    return model, tokenizer


def tokenize_text(tokenizer: Any, text: str, max_length: int) -> Any:
    """Tokenize one text input for causal-LM hidden-state projection."""

    if max_length <= 0:
        raise ValueError("max_length must be positive.")
    if not isinstance(text, str):
        raise TypeError(f"text must be a string, got {type(text).__name__}.")
    return tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=max_length,
        padding=False,
    )


def compute_hidden_states(model: Any, tokenizer: Any, text: str, max_length: int) -> tuple[Any, ...]:
    """Compute HuggingFace hidden states for one text input.

    The returned tuple follows HuggingFace `output_hidden_states=True`
    indexing: index 0 is the embedding output, index 1 is the first transformer
    block output, and index N is the output after transformer block N. These are
    hidden-state tuple indices, not Stage 4 model-layer indices.
    """

    import torch

    tokenized = tokenize_text(tokenizer, text, max_length)
    input_device = _model_input_device(model)
    model_inputs = {
        key: value.to(input_device) if hasattr(value, "to") else value
        for key, value in tokenized.items()
    }
    with torch.no_grad():
        outputs = model(**model_inputs, output_hidden_states=True)
    hidden_states = getattr(outputs, "hidden_states", None)
    if hidden_states is None:
        raise RuntimeError("Model output did not include hidden_states.")
    if not isinstance(hidden_states, tuple):
        hidden_states = tuple(hidden_states)
    if not hidden_states:
        raise RuntimeError("Model returned an empty hidden_states tuple.")
    return hidden_states


def _validate_hidden_state_tensor(hidden_state: Any, *, layer_index: int) -> None:
    if not hasattr(hidden_state, "ndim") or not hasattr(hidden_state, "shape"):
        raise TypeError(f"Hidden state {layer_index} is not a tensor-like object.")
    if hidden_state.ndim != 3:
        raise ValueError(
            f"Hidden state {layer_index} must have shape [batch, seq_len, hidden_dim], "
            f"got {tuple(hidden_state.shape)}."
        )
    if int(hidden_state.shape[0]) != 1:
        raise ValueError(
            f"Hidden state {layer_index} batch size must be 1 for per-token projection, "
            f"got batch size {int(hidden_state.shape[0])}."
        )


def _normalize_direction_tensor(direction: Any, *, hidden_dim: int, reference_tensor: Any) -> Any:
    import torch

    if not isinstance(direction, torch.Tensor):
        try:
            direction = torch.as_tensor(direction)
        except Exception as exc:
            raise TypeError(
                f"Refusal direction must be convertible to a torch.Tensor, got {type(direction).__name__}."
            ) from exc
    direction = direction.squeeze()
    if direction.ndim != 1:
        raise ValueError(
            "Refusal direction must be a 1D vector after squeezing singleton dimensions, "
            f"got shape {tuple(direction.shape)}."
        )
    direction_dim = int(direction.shape[0])
    if direction_dim != hidden_dim:
        raise ValueError(
            "Refusal direction dimension does not match model hidden size: "
            f"direction has {direction_dim}, hidden states have {hidden_dim}."
        )
    return direction.to(device=reference_tensor.device, dtype=reference_tensor.dtype)


def _selected_layer_indices(hidden_states: tuple[Any, ...], layers: Optional[list[int]]) -> list[int]:
    if layers is None:
        return list(range(len(hidden_states)))
    if not layers:
        raise ValueError("layers must be None or a non-empty list of hidden-state indices.")

    selected: list[int] = []
    for layer in layers:
        if not isinstance(layer, int):
            raise TypeError(f"Layer indices must be integers, got {type(layer).__name__}.")
        if layer < 0 or layer >= len(hidden_states):
            raise ValueError(
                f"Layer index {layer} is out of range for hidden_states of length {len(hidden_states)}. "
                "Layer indices are HuggingFace hidden-state tuple indices: "
                "0 is embeddings, 1 is the first transformer block output."
            )
        selected.append(layer)
    return selected


def compute_layer_token_projections(
    hidden_states: tuple[Any, ...],
    direction: Any,
    layers: Optional[list[int]] = None,
) -> dict[int, Any]:
    """Project hidden states onto a refusal direction for selected layers.

    Returned keys are HuggingFace hidden-state tuple indices: 0 is the embedding
    output, 1 is the first transformer block output, and N is the output after
    transformer block N. Do not interpret these as Stage 4 model-layer indices;
    Stage 4 layer 0 corresponds to the first transformer block, not embeddings.

    Values are `[seq_len]` tensors, one scalar projection per token.
    """

    if not isinstance(hidden_states, tuple):
        hidden_states = tuple(hidden_states)
    if not hidden_states:
        raise ValueError("hidden_states must contain at least one tensor.")

    selected_layers = _selected_layer_indices(hidden_states, layers)
    projections: dict[int, Any] = {}
    hidden_dim: int | None = None
    direction_tensor = None

    for layer_index in selected_layers:
        hidden_state = hidden_states[layer_index]
        _validate_hidden_state_tensor(hidden_state, layer_index=layer_index)
        layer_hidden_dim = int(hidden_state.shape[-1])
        if hidden_dim is None:
            hidden_dim = layer_hidden_dim
            direction_tensor = _normalize_direction_tensor(
                direction,
                hidden_dim=hidden_dim,
                reference_tensor=hidden_state,
            )
        elif layer_hidden_dim != hidden_dim:
            raise ValueError(
                "All selected hidden states must share the same hidden_dim, "
                f"but layer {layer_index} has {layer_hidden_dim} and earlier layers have {hidden_dim}."
            )
        assert direction_tensor is not None
        direction_for_layer = direction_tensor.to(device=hidden_state.device, dtype=hidden_state.dtype)
        projections[layer_index] = hidden_state[0] @ direction_for_layer

    return projections


def _input_sequence_length(input_ids: Any) -> int:
    if not hasattr(input_ids, "ndim") or not hasattr(input_ids, "shape"):
        raise TypeError("input_ids must be a tensor-like object with shape [seq_len] or [1, seq_len].")
    if input_ids.ndim == 1:
        return int(input_ids.shape[0])
    if input_ids.ndim == 2 and int(input_ids.shape[0]) == 1:
        return int(input_ids.shape[1])
    raise ValueError(
        "input_ids must have shape [seq_len] or [1, seq_len], "
        f"got {tuple(input_ids.shape)}."
    )


def _region_slice(region: str, seq_len: int) -> slice:
    if region == "all":
        return slice(0, seq_len)
    if region == "first_32":
        return slice(0, min(32, seq_len))
    if region == "last_32":
        return slice(max(0, seq_len - 32), seq_len)
    if region == "last_16":
        return slice(max(0, seq_len - 16), seq_len)
    if region == "last_8":
        return slice(max(0, seq_len - 8), seq_len)
    if region == "final_token":
        return slice(max(0, seq_len - 1), seq_len)
    raise ValueError(
        f"Unsupported token region {region!r}. Supported regions: {sorted(SUPPORTED_TOKEN_REGIONS)}."
    )


def _summarize_values(values: Any) -> dict[str, float | int]:
    if int(values.numel()) == 0:
        raise ValueError("Cannot summarize an empty token region.")
    values_float = values.detach().float().cpu()
    return {
        "mean": float(values_float.mean().item()),
        "max": float(values_float.max().item()),
        "min": float(values_float.min().item()),
        "final": float(values_float[-1].item()),
        "abs_mean": float(values_float.abs().mean().item()),
        "num_tokens": int(values_float.numel()),
    }


def summarize_token_regions(
    projections: dict[int, Any],
    input_ids: Any,
    tokenizer: Any,
    token_regions: list[str],
) -> dict[int, dict[str, dict[str, float | int]]]:
    """Summarize projection tensors over configured token regions.

    This function intentionally does not decode, print, or return token text.
    `tokenizer` is accepted for API symmetry with later Stage 5 wiring but is
    unused here.
    """

    del tokenizer
    if not projections:
        raise ValueError("projections must contain at least one layer.")
    if not token_regions:
        raise ValueError("token_regions must contain at least one region name.")

    seq_len = _input_sequence_length(input_ids)
    summaries: dict[int, dict[str, dict[str, float | int]]] = {}
    for layer_index, projection in projections.items():
        if not hasattr(projection, "ndim") or not hasattr(projection, "shape"):
            raise TypeError(f"Projection for layer {layer_index} is not a tensor-like object.")
        if projection.ndim != 1:
            raise ValueError(
                f"Projection for layer {layer_index} must have shape [seq_len], "
                f"got {tuple(projection.shape)}."
            )
        if int(projection.shape[0]) != seq_len:
            raise ValueError(
                f"Projection length for layer {layer_index} ({int(projection.shape[0])}) "
                f"does not match input_ids sequence length ({seq_len})."
            )

        layer_summary: dict[str, dict[str, float | int]] = {}
        for region in token_regions:
            region_window = _region_slice(region, seq_len)
            layer_summary[region] = _summarize_values(projection[region_window])
        summaries[int(layer_index)] = layer_summary

    return summaries


def compute_projection_dynamics(*args: object, **kwargs: object) -> None:
    """Placeholder for future refusal-direction projection computation."""

    raise NotImplementedError(
        "Stage 5 projection dynamics are not implemented yet. "
        "This skeleton must not load models or run inference."
    )


# TODO(stage5): Parse token regions, capture activations, and project activations onto refusal directions.
