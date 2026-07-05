"""
Deterministic reference cache for Stage GCG-Early.

For each surrogate task, caches the hidden states of the model's forward pass
on the neutral-suffix reference input. The cache key includes all configuration
fields that can affect activations: model revision, tokenizer revision,
chat-template hash, thinking mode, suffix string, layers, and positions.

Cache invalidation is strict: if a cache entry exists but was built under a
different configuration, raise CacheKeyMismatchError rather than silently
returning stale data.

Disk layout inside <output_dir>/reference_cache/:
  REFERENCE_CACHE_MANIFEST.json   — index of all entries (one JSON object per line)
  {task_id}_{cache_key_short}.pt  — {
        "input_ids": list[int],
        "hidden_states": {str(layer): {str(pos): tensor}},
        "metadata": {...}
  }
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage_gcg_early.model_adapter import (
    apply_chat_template,
    tokenize_continuation,
    tokenize_prompt,
)
from poc_stage_gcg_early.suffix_token_manager import build_suffix_spans
from poc_stage_gcg_early.selected_state_capture import capture_selected_states


class CacheKeyMismatchError(Exception):
    """Raised when a cache entry exists but was built under a different configuration."""


@dataclass
class ReferenceCacheEntry:
    task_id: str
    cache_key: str                    # first 16 hex chars of SHA-256
    input_ids: List[int]              # reference full token IDs
    hidden_states: Dict               # {layer_idx: {token_pos: tensor}}
    tokenizer_revision: Optional[str]
    model_revision: Optional[str]
    chat_template_hash: str
    enable_thinking: bool
    dtype: str
    created_at: str                   # ISO 8601 UTC
    layers: List[int]
    positions: List[int]


def _compute_cache_key(fields: dict) -> str:
    """SHA-256 of sorted JSON of all config fields that affect activations."""
    serialized = json.dumps(fields, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()[:16]


def _chat_template_hash(tokenizer: Any) -> str:
    """Hash of the tokenizer's chat template string to detect template changes."""
    tmpl = getattr(tokenizer, "chat_template", None) or ""
    return hashlib.sha256(tmpl.encode()).hexdigest()[:8]


def _tokenizer_revision(tokenizer: Any) -> Optional[str]:
    try:
        return str(tokenizer.name_or_path)
    except AttributeError:
        return None


def _model_revision(model: Any) -> Optional[str]:
    try:
        return str(model.config._commit_hash or model.config.name_or_path)
    except AttributeError:
        return None


class ReferenceCache:
    """
    Persistent cache of reference hidden states for each surrogate task.

    Usage:
        cache = ReferenceCache(cache_dir)
        entry = cache.get_or_build(
            task_id, model, tokenizer, model_family,
            neutral_suffix, enable_thinking, layers, positions
        )
    """

    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._manifest_path = self.cache_dir / "REFERENCE_CACHE_MANIFEST.json"
        self._manifest: Dict[str, dict] = {}
        self._load_manifest()

    # ------------------------------------------------------------------
    # Manifest management
    # ------------------------------------------------------------------

    def _load_manifest(self) -> None:
        if self._manifest_path.exists():
            with open(self._manifest_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entry = json.loads(line)
                        self._manifest[entry["task_id"]] = entry

    def _append_manifest(self, entry_meta: dict) -> None:
        with open(self._manifest_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry_meta, ensure_ascii=True) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def _tensor_path(self, task_id: str, cache_key: str) -> Path:
        safe_task_id = task_id.replace("/", "_").replace(" ", "_")
        return self.cache_dir / f"{safe_task_id}_{cache_key}.pt"

    # ------------------------------------------------------------------
    # Key computation
    # ------------------------------------------------------------------

    def _make_key_fields(
        self,
        task_id: str,
        model: Any,
        tokenizer: Any,
        model_family: str,
        neutral_suffix: str,
        enable_thinking: bool,
        layers: List[int],
        positions: List[int],
    ) -> dict:
        return {
            "task_id": task_id,
            "model_family": model_family,
            "model_revision": _model_revision(model),
            "tokenizer_revision": _tokenizer_revision(tokenizer),
            "chat_template_hash": _chat_template_hash(tokenizer),
            "enable_thinking": enable_thinking,
            "neutral_suffix": neutral_suffix,
            "layers": sorted(layers),
            "positions": sorted(positions),
            "dtype": "float16",
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def assert_not_stale(
        self,
        task_id: str,
        model: Any,
        tokenizer: Any,
        model_family: str,
        neutral_suffix: str,
        enable_thinking: bool,
        layers: List[int],
        positions: List[int],
    ) -> None:
        """
        Raise CacheKeyMismatchError if a cache entry exists for task_id but
        was built under a different configuration (would return stale data).
        """
        if task_id not in self._manifest:
            return
        existing = self._manifest[task_id]
        key_fields = self._make_key_fields(
            task_id, model, tokenizer, model_family,
            neutral_suffix, enable_thinking, layers, positions,
        )
        expected_key = _compute_cache_key(key_fields)
        if existing["cache_key"] != expected_key:
            raise CacheKeyMismatchError(
                f"Cache entry for task '{task_id}' exists under key "
                f"{existing['cache_key']} but current config computes "
                f"key {expected_key}. Delete the stale cache entry or "
                f"use a new output directory."
            )

    def get(
        self,
        task_id: str,
        model: Any,
        tokenizer: Any,
        model_family: str,
        neutral_suffix: str,
        enable_thinking: bool,
        layers: List[int],
        positions: List[int],
    ) -> Optional[ReferenceCacheEntry]:
        """Return cached entry or None if not found."""
        self.assert_not_stale(
            task_id, model, tokenizer, model_family,
            neutral_suffix, enable_thinking, layers, positions,
        )
        if task_id not in self._manifest:
            return None
        meta = self._manifest[task_id]
        pt_path = self._tensor_path(task_id, meta["cache_key"])
        if not pt_path.exists():
            return None
        data = torch.load(pt_path, map_location="cpu", weights_only=False)
        # Reconstruct hidden_states dict with integer keys
        hs_raw = data["hidden_states"]
        hs = {
            int(l): {int(p): v for p, v in pos_dict.items()}
            for l, pos_dict in hs_raw.items()
        }
        return ReferenceCacheEntry(
            task_id=task_id,
            cache_key=meta["cache_key"],
            input_ids=data["input_ids"],
            hidden_states=hs,
            tokenizer_revision=meta.get("tokenizer_revision"),
            model_revision=meta.get("model_revision"),
            chat_template_hash=meta.get("chat_template_hash", ""),
            enable_thinking=meta.get("enable_thinking", enable_thinking),
            dtype=meta.get("dtype", "float16"),
            created_at=meta.get("created_at", ""),
            layers=meta.get("layers", layers),
            positions=meta.get("positions", positions),
        )

    def build_and_store(
        self,
        task_id: str,
        instruction: str,
        model: Any,
        tokenizer: Any,
        model_family: str,
        neutral_suffix: str,
        enable_thinking: bool,
        layers: List[int],
        positions: List[int],
        suffix_ids_override: Optional[List[int]] = None,
    ) -> ReferenceCacheEntry:
        """
        Run a forward pass on the neutral-suffix input and store the result.

        Skips silently if the entry already exists with the same config key.
        Raises CacheKeyMismatchError if a different config's entry exists.

        suffix_ids_override: if provided, use these token IDs directly for the
          neutral suffix (bypasses BPE tokenization). Required when the neutral
          suffix is specified as raw token IDs (e.g. [220]*16 for Stage 8b).
        """
        self.assert_not_stale(
            task_id, model, tokenizer, model_family,
            neutral_suffix, enable_thinking, layers, positions,
        )
        if task_id in self._manifest:
            # Already built — return cached
            return self.get(
                task_id, model, tokenizer, model_family,
                neutral_suffix, enable_thinking, layers, positions,
            )

        # Build the reference input (neutral suffix)
        spans = build_suffix_spans(
            tokenizer, model_family, enable_thinking,
            instruction, neutral_suffix, safe_target=" ",
            suffix_ids_override=suffix_ids_override,
        )
        input_ids = spans.input_ids  # full [prefix + neutral_suffix + " "]

        # Capture hidden states at requested layers and positions
        # Positions are within the prefix+suffix region (before the single target token)
        ref_positions = [p for p in positions if p < len(spans.input_ids)]
        hs = capture_selected_states(
            model, input_ids, layers, ref_positions, preserve_grad=False
        )

        # Serialize hidden states with string keys (JSON-safe)
        hs_serializable = {
            str(l): {str(p): v for p, v in pos_dict.items()}
            for l, pos_dict in hs.items()
        }

        key_fields = self._make_key_fields(
            task_id, model, tokenizer, model_family,
            neutral_suffix, enable_thinking, layers, positions,
        )
        cache_key = _compute_cache_key(key_fields)
        created_at = datetime.now(timezone.utc).isoformat()

        pt_path = self._tensor_path(task_id, cache_key)
        torch.save(
            {
                "input_ids": input_ids.tolist(),
                "hidden_states": hs_serializable,
                "metadata": {
                    "task_id": task_id,
                    "cache_key": cache_key,
                    "layers": layers,
                    "positions": positions,
                    "created_at": created_at,
                },
            },
            pt_path,
        )

        meta = {
            "task_id": task_id,
            "cache_key": cache_key,
            "model_revision": _model_revision(model),
            "tokenizer_revision": _tokenizer_revision(tokenizer),
            "chat_template_hash": _chat_template_hash(tokenizer),
            "enable_thinking": enable_thinking,
            "neutral_suffix": neutral_suffix,
            "layers": sorted(layers),
            "positions": sorted(positions),
            "dtype": "float16",
            "created_at": created_at,
            "pt_path": str(pt_path.name),
        }
        self._manifest[task_id] = meta
        self._append_manifest(meta)

        return ReferenceCacheEntry(
            task_id=task_id,
            cache_key=cache_key,
            input_ids=input_ids.tolist(),
            hidden_states={int(l): {int(p): v for p, v in pd.items()} for l, pd in hs.items()},
            tokenizer_revision=meta["tokenizer_revision"],
            model_revision=meta["model_revision"],
            chat_template_hash=meta["chat_template_hash"],
            enable_thinking=enable_thinking,
            dtype="float16",
            created_at=created_at,
            layers=layers,
            positions=positions,
        )

    def get_or_build(
        self,
        task_id: str,
        instruction: str,
        model: Any,
        tokenizer: Any,
        model_family: str,
        neutral_suffix: str,
        enable_thinking: bool,
        layers: List[int],
        positions: List[int],
    ) -> ReferenceCacheEntry:
        """Get from cache or build if missing."""
        cached = self.get(
            task_id, model, tokenizer, model_family,
            neutral_suffix, enable_thinking, layers, positions,
        )
        if cached is not None:
            return cached
        return self.build_and_store(
            task_id, instruction, model, tokenizer, model_family,
            neutral_suffix, enable_thinking, layers, positions,
        )
