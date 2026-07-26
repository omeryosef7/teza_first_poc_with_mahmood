"""Regression test for the enable_thinking=False silent no-op fix in
poc_stage4/qwen3_model.py::Qwen3Model.format_prompts (2026-07-26).

Before the fix, enable_thinking=False was NOT passed to apply_chat_template (only True was),
so Qwen3's thinking-ON template default silently applied. This test uses a mock tokenizer that
records the kwargs it receives, and asserts the flag is now passed EXPLICITLY for BOTH values.
Torch-free; bypasses Qwen3Model.__init__ (no model/weights loaded).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from poc_stage4.qwen3_model import Qwen3Model  # noqa: E402


class _RecordingTokenizer:
    """apply_chat_template that records the kwargs it was called with and renders
    a template whose thinking-block presence depends on enable_thinking (like Qwen3)."""

    def __init__(self):
        self.calls = []

    def apply_chat_template(self, messages, **kwargs):
        self.calls.append(kwargs)
        # Emulate Qwen3: enable_thinking omitted OR True => no empty think block;
        # enable_thinking=False => inject an empty <think></think>.
        et = kwargs.get("enable_thinking", "OMITTED")
        base = "<|im_start|>assistant\n"
        if et is False:
            base += "<think>\n\n</think>\n\n"
        return base


def _make_model_with(tok):
    m = object.__new__(Qwen3Model)  # bypass __init__ (no weights)
    m.tokenizer = tok
    return m


def test_enable_thinking_true_passes_flag_true():
    tok = _RecordingTokenizer()
    m = _make_model_with(tok)
    out = m.format_prompts(["hi"], enable_thinking=True)
    assert tok.calls[-1].get("enable_thinking") is True
    assert "<think>" not in out[0]


def test_enable_thinking_false_now_passes_flag_false_not_omitted():
    """THE FIX: False must be PASSED (not omitted), and must yield the empty-think prompt."""
    tok = _RecordingTokenizer()
    m = _make_model_with(tok)
    out = m.format_prompts(["hi"], enable_thinking=False)
    assert "enable_thinking" in tok.calls[-1], "enable_thinking=False was omitted (the old no-op bug)"
    assert tok.calls[-1]["enable_thinking"] is False
    assert "<think>\n\n</think>" in out[0], "thinking-OFF empty-think block not produced"


def test_thinking_on_vs_off_differ():
    tok = _RecordingTokenizer()
    m = _make_model_with(tok)
    on = m.format_prompts(["x"], enable_thinking=True)[0]
    off = m.format_prompts(["x"], enable_thinking=False)[0]
    assert on != off  # the whole point: the flag now actually changes the prompt


def test_typeerror_fallback_when_tokenizer_lacks_kwarg():
    class _NoKwargTok:
        def __init__(self):
            self.n = 0

        def apply_chat_template(self, messages, **kwargs):
            if "enable_thinking" in kwargs:
                raise TypeError("unexpected kwarg enable_thinking")
            self.n += 1
            return "PLAIN"

    tok = _NoKwargTok()
    m = _make_model_with(tok)
    out = m.format_prompts(["x"], enable_thinking=False)
    assert out == ["PLAIN"]  # fell back gracefully, no crash
