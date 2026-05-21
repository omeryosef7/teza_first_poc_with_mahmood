from __future__ import annotations

import inspect
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


VECTOR_KEYS = (
    "direction",
    "refusal_direction",
    "vector",
    "mean_difference",
    "probe_direction",
)


@dataclass(frozen=True)
class RefusalDirection:
    vector: Any
    source_path: str
    metadata: dict


def validate_direction_path(path: str | Path) -> Path:
    """Validate direction artifact presence."""

    direction_path = Path(path)
    if not direction_path.exists():
        raise FileNotFoundError(f"Direction artifact does not exist: {direction_path}")
    if not direction_path.is_file():
        raise ValueError(f"Direction artifact is not a file: {direction_path}")
    return direction_path


def _is_torch_tensor(value: Any) -> bool:
    return value.__class__.__module__.startswith("torch") and hasattr(value, "dim")


def _is_numpy_array(value: Any) -> bool:
    return value.__class__.__module__.startswith("numpy") and hasattr(value, "ndim")


def _shape(value: Any) -> tuple[int, ...]:
    shape = getattr(value, "shape", None)
    if shape is not None:
        return tuple(int(item) for item in shape)
    if isinstance(value, (list, tuple)):
        if value and isinstance(value[0], (list, tuple)):
            return (len(value), len(value[0]))
        return (len(value),)
    raise TypeError(f"Unsupported vector type: {type(value).__name__}")


def _squeeze_singleton_vector(vector: Any) -> Any:
    shape = _shape(vector)
    if len(shape) == 1:
        return vector
    if len(shape) == 2 and 1 in shape:
        if _is_torch_tensor(vector) or _is_numpy_array(vector):
            return vector.squeeze()
        if isinstance(vector, (list, tuple)):
            if shape[0] == 1:
                return list(vector[0])
            return [row[0] for row in vector]
    raise ValueError(
        "Refusal direction vector must be 1D. Singleton 2D vectors shaped "
        f"[1, hidden_dim] or [hidden_dim, 1] are accepted, but got shape {shape}."
    )


def _to_float_list(vector: Any) -> list[float]:
    if _is_torch_tensor(vector):
        return [float(item) for item in vector.detach().cpu().tolist()]
    if _is_numpy_array(vector):
        return [float(item) for item in vector.tolist()]
    if isinstance(vector, (list, tuple)):
        return [float(item) for item in vector]
    raise TypeError(f"Unsupported vector type: {type(vector).__name__}")


def _validate_finite_nonzero(vector: Any, *, eps: float) -> float:
    values = _to_float_list(vector)
    if not values:
        raise ValueError("Refusal direction vector is empty.")
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Refusal direction vector contains non-finite values.")
    norm = math.sqrt(sum(value * value for value in values))
    if norm <= eps:
        raise ValueError("Refusal direction vector has zero or near-zero norm.")
    return norm


def _cast_torch(vector: Any, *, device: str | None, dtype: str | None) -> Any:
    kwargs: dict[str, Any] = {}
    if device and device != "auto":
        kwargs["device"] = device
    if dtype and dtype != "auto":
        import torch

        if not hasattr(torch, dtype):
            raise ValueError(f"Unknown torch dtype: {dtype}")
        kwargs["dtype"] = getattr(torch, dtype)
    return vector.to(**kwargs) if kwargs else vector


def _cast_numpy(vector: Any, *, dtype: str | None) -> Any:
    if dtype and dtype != "auto":
        return vector.astype(dtype)
    return vector


def _normalize_torch(vector: Any, *, eps: float, device: str | None, dtype: str | None) -> Any:
    vector = _cast_torch(vector, device=device, dtype=dtype)
    norm = vector.norm()
    if float(norm.detach().cpu().item()) <= eps:
        raise ValueError("Refusal direction vector has zero or near-zero norm.")
    return vector / norm


def _normalize_numpy(vector: Any, *, eps: float, dtype: str | None) -> Any:
    vector = _cast_numpy(vector, dtype=dtype)
    norm = float((vector * vector).sum() ** 0.5)
    if norm <= eps:
        raise ValueError("Refusal direction vector has zero or near-zero norm.")
    return vector / norm


def normalize_direction(
    vector: Any,
    eps: float = 1e-12,
    *,
    device: str | None = None,
    dtype: str | None = None,
) -> Any:
    """Validate and normalize a refusal direction vector to unit norm."""

    vector = _squeeze_singleton_vector(vector)
    _validate_finite_nonzero(vector, eps=eps)
    if _is_torch_tensor(vector):
        return _normalize_torch(vector, eps=eps, device=device, dtype=dtype)
    if _is_numpy_array(vector):
        return _normalize_numpy(vector, eps=eps, dtype=dtype)
    values = _to_float_list(vector)
    norm = math.sqrt(sum(value * value for value in values))
    return [value / norm for value in values]


def _safe_torch_load(path: Path, *, device: str | None) -> Any:
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError(
            "Loading .pt/.pth refusal directions requires torch in the active Python environment."
        ) from exc

    kwargs: dict[str, Any] = {}
    if device and device != "auto":
        kwargs["map_location"] = device
    if "weights_only" in inspect.signature(torch.load).parameters:
        try:
            return torch.load(path, weights_only=True, **kwargs)
        except TypeError:
            pass
    return torch.load(path, **kwargs)


def _load_numpy(path: Path) -> tuple[Any, dict[str, Any]]:
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "Loading .npy/.npz refusal directions requires numpy in the active Python environment."
        ) from exc

    payload = np.load(path, allow_pickle=False)
    if path.suffix.lower() == ".npy":
        return payload, {"artifact_format": "npy", "selected_vector_key": None}

    files = list(payload.files)
    for key in VECTOR_KEYS:
        if key in files:
            return payload[key], {"artifact_format": "npz", "selected_vector_key": key, "npz_keys": files}
    if len(files) == 1:
        key = files[0]
        return payload[key], {"artifact_format": "npz", "selected_vector_key": key, "npz_keys": files}
    raise ValueError(
        "Unable to find a refusal direction vector in NPZ artifact. "
        f"Looked for keys {list(VECTOR_KEYS)}; available keys: {files}"
    )


def _extract_from_dict(payload: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    for key in VECTOR_KEYS:
        if key in payload:
            metadata = {
                item_key: item_value
                for item_key, item_value in payload.items()
                if item_key != key
            }
            metadata["selected_vector_key"] = key
            return payload[key], metadata
    raise ValueError(
        "Unable to find a refusal direction vector in dictionary artifact. "
        f"Looked for keys: {list(VECTOR_KEYS)}"
    )


def _load_json(path: Path) -> tuple[Any, dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        return payload, {"artifact_format": "json", "selected_vector_key": None}
    if isinstance(payload, dict):
        vector, metadata = _extract_from_dict(payload)
        metadata["artifact_format"] = "json"
        return vector, metadata
    raise ValueError("JSON refusal direction artifact must be a list or object.")


def _load_artifact(path: Path, *, device: str | None) -> tuple[Any, dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix in {".pt", ".pth"}:
        payload = _safe_torch_load(path, device=device)
        if isinstance(payload, dict):
            vector, metadata = _extract_from_dict(payload)
            metadata["artifact_format"] = suffix.lstrip(".")
            return vector, metadata
        return payload, {"artifact_format": suffix.lstrip("."), "selected_vector_key": None}
    if suffix in {".npy", ".npz"}:
        return _load_numpy(path)
    if suffix == ".json":
        return _load_json(path)
    raise ValueError(f"Unsupported refusal direction artifact extension: {suffix}")


def load_refusal_direction(path: str | Path, device: str | None = None, dtype: str | None = None) -> RefusalDirection:
    """Load, validate, and unit-normalize a refusal direction vector."""

    direction_path = validate_direction_path(path)
    vector, metadata = _load_artifact(direction_path, device=device)
    normalized = normalize_direction(vector, device=device, dtype=dtype)
    metadata = {
        **metadata,
        "normalized": True,
        "source_path": str(direction_path),
    }
    return RefusalDirection(
        vector=normalized,
        source_path=str(direction_path),
        metadata=metadata,
    )


def _self_test() -> None:
    """Small internal smoke test; intentionally not run automatically."""

    import tempfile

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json") as handle:
        json.dump([3.0, 4.0], handle)
        handle.flush()
        loaded = load_refusal_direction(handle.name)
    assert _shape(loaded.vector) == (2,)
    assert abs(_validate_finite_nonzero(loaded.vector, eps=1e-12) - 1.0) < 1e-12

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json") as handle:
        json.dump({"metadata": {"name": "demo"}, "vector": [[0.0, 2.0]]}, handle)
        handle.flush()
        loaded = load_refusal_direction(handle.name)
    assert _shape(loaded.vector) == (2,)
    assert loaded.metadata["selected_vector_key"] == "vector"

    for bad_vector in ([[1.0, 2.0], [3.0, 4.0]], [float("nan")], [0.0, 0.0]):
        try:
            normalize_direction(bad_vector)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected invalid vector to fail: {bad_vector}")
