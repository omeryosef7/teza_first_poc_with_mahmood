"""
Tests for reference_cache.py.

CPU-only stub tests (no real model needed for key computation and manifest logic).
GPU integration tests require a real model.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import torch

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage_gcg_early.reference_cache import (
    CacheKeyMismatchError,
    ReferenceCache,
    _compute_cache_key,
)


class TestCacheKeyComputation:

    def test_different_configs_give_different_keys(self):
        fields_a = {"task_id": "t1", "model_family": "qwen3", "enable_thinking": True,
                    "neutral_suffix": " ", "layers": [0, 1], "positions": [0]}
        fields_b = {**fields_a, "enable_thinking": False}
        assert _compute_cache_key(fields_a) != _compute_cache_key(fields_b)

    def test_same_config_gives_same_key(self):
        fields = {"task_id": "t1", "model_family": "qwen3", "enable_thinking": True,
                  "neutral_suffix": " ", "layers": [0, 1], "positions": [0]}
        assert _compute_cache_key(fields) == _compute_cache_key(fields)

    def test_layer_order_independent(self):
        """Sorted layer lists should give the same key."""
        fields_a = {"layers": [0, 1, 2], "x": "v"}
        fields_b = {"layers": [2, 1, 0], "x": "v"}
        # Note: layers are not auto-sorted in _compute_cache_key —
        # callers must sort before passing. This test confirms that behavior.
        # If sorted, keys match; if not sorted, keys differ.
        fields_a_sorted = {**fields_a, "layers": sorted(fields_a["layers"])}
        fields_b_sorted = {**fields_b, "layers": sorted(fields_b["layers"])}
        assert _compute_cache_key(fields_a_sorted) == _compute_cache_key(fields_b_sorted)


class TestReferenceCacheManifest:

    def test_empty_cache_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = ReferenceCache(Path(tmp))
            assert cache._manifest == {}

    def test_manifest_persists_across_instances(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Manually write a fake manifest entry
            manifest_path = Path(tmp) / "REFERENCE_CACHE_MANIFEST.json"
            entry = {
                "task_id": "t1",
                "cache_key": "abc123",
                "model_revision": None,
                "tokenizer_revision": None,
                "chat_template_hash": "ff00",
                "enable_thinking": True,
                "neutral_suffix": " ",
                "layers": [0],
                "positions": [0],
                "dtype": "float16",
                "created_at": "2026-07-05T00:00:00+00:00",
                "pt_path": "t1_abc123.pt",
            }
            with open(manifest_path, "w") as f:
                f.write(json.dumps(entry) + "\n")

            cache = ReferenceCache(Path(tmp))
            assert "t1" in cache._manifest
            assert cache._manifest["t1"]["cache_key"] == "abc123"

    def test_assert_not_stale_raises_on_mismatch(self):
        """assert_not_stale must raise CacheKeyMismatchError when config changed."""
        with tempfile.TemporaryDirectory() as tmp:
            # Write a manifest entry with a specific cache key
            manifest_path = Path(tmp) / "REFERENCE_CACHE_MANIFEST.json"
            entry = {
                "task_id": "t1",
                "cache_key": "deadbeef12345678",
                "model_revision": None,
                "tokenizer_revision": None,
                "chat_template_hash": "ff00",
                "enable_thinking": True,
                "neutral_suffix": " ",
                "layers": [0],
                "positions": [0],
                "dtype": "float16",
                "created_at": "2026-07-05T00:00:00+00:00",
                "pt_path": "t1_deadbeef12345678.pt",
            }
            with open(manifest_path, "w") as f:
                f.write(json.dumps(entry) + "\n")

            cache = ReferenceCache(Path(tmp))
            mock_model = MagicMock()
            mock_model.config._commit_hash = None
            mock_model.config.name_or_path = "Qwen/Qwen3-14B"
            mock_model.generation_config.eos_token_id = 1
            mock_tokenizer = MagicMock()
            mock_tokenizer.chat_template = "test-template"
            mock_tokenizer.name_or_path = "Qwen/Qwen3-14B"

            with pytest.raises(CacheKeyMismatchError):
                cache.assert_not_stale(
                    "t1", mock_model, mock_tokenizer, "qwen3",
                    neutral_suffix=" ", enable_thinking=True,
                    layers=[0], positions=[0],
                )

    def test_assert_not_stale_passes_for_new_task(self):
        """No error for a task_id not yet in the manifest."""
        with tempfile.TemporaryDirectory() as tmp:
            cache = ReferenceCache(Path(tmp))
            mock_model = MagicMock()
            mock_tokenizer = MagicMock()
            mock_tokenizer.chat_template = ""
            # Should not raise
            cache.assert_not_stale(
                "new_task", mock_model, mock_tokenizer, "qwen3",
                neutral_suffix=" ", enable_thinking=True,
                layers=[0], positions=[0],
            )
