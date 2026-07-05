"""
Pytest configuration and shared fixtures for Stage GCG-Early tests.

All fixtures here are CPU-only (no real Qwen3/Gemma4 models).
GPU integration tests are marked @pytest.mark.gpu_integration and
must be run explicitly with: pytest -m gpu_integration
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import torch
import torch.nn as nn

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "gpu_integration: mark test as requiring a real GPU and full model"
    )


# ---------------------------------------------------------------------------
# Tiny toy tokenizer (no HuggingFace required)
# ---------------------------------------------------------------------------

class ToyTokenizer:
    """
    Minimal tokenizer for testing suffix/target slice logic.

    Vocabulary: {'[BOS]': 0, '[EOS]': 1, '[PAD]': 2, '!': 3, ' ': 4,
                 'A': 5, 'B': 6, 'C': 7, 'Apple': 8, 'Banana': 9, ',': 10, '.': 11,
                 'List': 12, 'three': 13, 'fruits': 14, '[USER]': 15, '[ASSISTANT]': 16,
                 'Cherry': 17, 'think': 18, '/think': 19, '\n': 20}
    chat_template: "[BOS][USER]{content}[ASSISTANT]"
    """
    _vocab = {
        "[BOS]": 0, "[EOS]": 1, "[PAD]": 2,
        "!": 3, " ": 4,
        "A": 5, "B": 6, "C": 7,
        "Apple": 8, "Banana": 9, ",": 10, ".": 11,
        "List": 12, "three": 13, "fruits": 14,
        "[USER]": 15, "[ASSISTANT]": 16, "Cherry": 17,
        "think": 18, "/think": 19, "\n": 20, "five": 21,
    }
    _inv_vocab = {v: k for k, v in _vocab.items()}
    eos_token_id = 1
    pad_token_id = 2
    chat_template = "[BOS][USER]{content}[ASSISTANT]"

    def __call__(self, text, add_special_tokens=True, return_tensors=None):
        ids = self._encode(text)
        if return_tensors == "pt":
            return MagicMock(input_ids=torch.tensor([ids]))
        result = MagicMock()
        result.input_ids = ids
        return result

    def _encode(self, text: str):
        # Simple whitespace + special-token tokenization
        tokens = []
        for word in text.replace("[BOS]", " [BOS] ").replace("[EOS]", " [EOS] ").replace(
                "[USER]", " [USER] ").replace("[ASSISTANT]", " [ASSISTANT] ").split():
            if word in self._vocab:
                tokens.append(self._vocab[word])
            else:
                # character-level fallback
                for ch in word:
                    tokens.append(self._vocab.get(ch, 2))
        return tokens

    def decode(self, ids, skip_special_tokens=True):
        parts = []
        for i in ids:
            tok = self._inv_vocab.get(i, "?")
            if skip_special_tokens and tok in ("[BOS]", "[EOS]", "[PAD]", "[USER]", "[ASSISTANT]"):
                continue
            parts.append(tok)
        return "".join(parts)

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True,
                            enable_thinking=False, **kwargs):
        content = messages[0]["content"]
        result = f"[BOS][USER]{content}[ASSISTANT]"
        return result


@pytest.fixture
def toy_tokenizer():
    return ToyTokenizer()


# ---------------------------------------------------------------------------
# Tiny toy model (2-layer transformer, CPU)
# ---------------------------------------------------------------------------

class TinyDecoderLayer(nn.Module):
    def __init__(self, d_model: int):
        super().__init__()
        self.linear = nn.Linear(d_model, d_model, bias=False)

    def forward(self, hidden_states, **kwargs):
        out = self.linear(hidden_states)
        return (out,)


class TinyModel(nn.Module):
    """
    2-layer toy causal LM for testing hook logic without real weights.
    Matches the attribute structure that Stage AE's _register_layer_hooks expects.
    """
    def __init__(self, vocab_size: int = 32, d_model: int = 16, n_layers: int = 2):
        super().__init__()
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.model = nn.ModuleDict({
            "embed_tokens": nn.Embedding(vocab_size, d_model),
        })
        # Layers as a list (matched by _register_layer_hooks)
        self.model.layers = nn.ModuleList([
            TinyDecoderLayer(d_model) for _ in range(n_layers)
        ])
        self.model.norm = nn.LayerNorm(d_model)
        self.lm_head = nn.Linear(d_model, vocab_size, bias=False)

        # Needed by model_adapter
        self.generation_config = MagicMock()
        self.generation_config.eos_token_id = 1

    @property
    def device(self):
        return next(self.parameters()).device

    def forward(self, input_ids=None, inputs_embeds=None, attention_mask=None,
                use_cache=False, output_hidden_states=False, **kwargs):
        if inputs_embeds is not None:
            x = inputs_embeds
        else:
            x = self.model["embed_tokens"](input_ids)

        all_hidden = [x] if output_hidden_states else None

        for layer in self.model.layers:
            x = layer(x)[0]
            if output_hidden_states:
                all_hidden.append(x)

        x = self.model.norm(x)
        if output_hidden_states:
            all_hidden[-1] = x  # replace last with normed

        logits = self.lm_head(x)

        result = MagicMock()
        result.logits = logits
        if output_hidden_states:
            result.hidden_states = [h.unsqueeze(0) if h.dim() == 2 else h for h in all_hidden]
        return result


@pytest.fixture
def tiny_model():
    model = TinyModel(vocab_size=32, d_model=16, n_layers=2)
    model.eval()
    return model
