from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional


PROMPT_FIELDS = ("full_prompt", "attack_prompt", "prompt", "input", "messages")
RESPONSE_FIELDS = ("target_response", "response", "model_response", "output")


@dataclass(frozen=True)
class Stage5Example:
    example_id: str
    goal_index: Optional[int]
    condition: str
    goal: Optional[str]
    prompt_text: str
    response_text: Optional[str]
    is_success: Optional[bool]
    judge_score: Optional[float]
    strongreject_score: Optional[float]
    source_path: str
    raw: dict

    def metadata(self) -> dict[str, Any]:
        """Return metadata only; intentionally excludes raw/prompt/response text."""

        return {
            "example_id": self.example_id,
            "goal_index": self.goal_index,
            "condition": self.condition,
            "has_response_text": self.response_text is not None,
            "is_success": self.is_success,
            "judge_score": self.judge_score,
            "strongreject_score": self.strongreject_score,
            "source_path": self.source_path,
        }


@dataclass(frozen=True)
class Stage5ExampleLoadResult:
    examples: list[Stage5Example]
    skipped_contentless_rows: int
    source_path: str

    @property
    def num_examples(self) -> int:
        return len(self.examples)

    @property
    def num_with_response_text(self) -> int:
        return sum(1 for example in self.examples if example.response_text is not None)

    @property
    def condition_values(self) -> list[str]:
        return sorted({example.condition for example in self.examples})

    @property
    def first_example_ids(self) -> list[str]:
        return [example.example_id for example in self.examples[:3]]


def validate_jsonl_path(path: str | Path) -> Path:
    """Validate that a JSONL input exists without normalizing its schema."""

    input_path = Path(path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input JSONL does not exist: {input_path}")
    if not input_path.is_file():
        raise ValueError(f"Input JSONL is not a file: {input_path}")
    return input_path


def iter_jsonl(path: str | Path) -> Iterator[dict[str, Any]]:
    """Yield JSON object rows from a JSONL file."""
    input_path = validate_jsonl_path(path)
    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} in {input_path}: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"Expected JSON object on line {line_number} in {input_path}.")
            yield row


def count_jsonl_rows(path: str | Path, *, max_rows: int | None = None) -> int:
    """Count non-empty JSONL object rows."""

    count = 0
    for _row in iter_jsonl(path):
        count += 1
        if max_rows is not None and count >= max_rows:
            break
    return count


def preview_jsonl_rows(path: str | Path, *, max_rows: int = 1) -> list[dict[str, Any]]:
    """Return a tiny raw preview only; Stage 5 normalization is a future TODO."""

    if max_rows <= 0:
        raise ValueError("max_rows must be positive.")
    rows: list[dict[str, Any]] = []
    for row in iter_jsonl(path):
        rows.append(row)
        if len(rows) >= max_rows:
            break
    return rows


def _coerce_int(value: Any) -> Optional[int]:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_float(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n"}:
            return False
    return None


def _text_or_none(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value)
    return text if text.strip() else None


def _messages_to_transcript(messages: Any) -> Optional[str]:
    if not isinstance(messages, list):
        return _text_or_none(messages)

    lines: list[str] = []
    for index, message in enumerate(messages):
        if isinstance(message, dict):
            role = str(message.get("role", f"message_{index}"))
            content = message.get("content")
            if isinstance(content, list):
                content_text = " ".join(
                    str(part.get("text", part)) if isinstance(part, dict) else str(part)
                    for part in content
                )
            else:
                content_text = "" if content is None else str(content)
            if content_text.strip():
                lines.append(f"{role}: {content_text}")
        else:
            text = str(message)
            if text.strip():
                lines.append(f"message_{index}: {text}")
    return "\n".join(lines) if lines else None


def _find_prompt_text(row: dict[str, Any]) -> Optional[str]:
    for field in PROMPT_FIELDS:
        if field not in row:
            continue
        if field == "messages":
            text = _messages_to_transcript(row.get(field))
        else:
            text = _text_or_none(row.get(field))
        if text is not None:
            return text
    return _text_or_none(row.get("goal"))


def _find_response_text(row: dict[str, Any]) -> Optional[str]:
    for field in RESPONSE_FIELDS:
        if field not in row:
            continue
        text = _text_or_none(row.get(field))
        if text is not None:
            return text
    return None


def _make_example_id(row: dict[str, Any], *, line_number: int) -> str:
    explicit = _text_or_none(row.get("example_id") or row.get("id"))
    if explicit is not None:
        return explicit

    parts = []
    for field in ("goal_index", "condition", "attack_iteration", "conversation_id", "target_model"):
        value = row.get(field)
        if value is not None:
            parts.append(f"{field}={value}")
    if parts:
        return "|".join(parts)
    return f"line={line_number}"


def _normalize_example(
    row: dict[str, Any],
    *,
    line_number: int,
    source_path: Path,
    default_condition: str | None,
) -> Stage5Example | None:
    prompt_text = _find_prompt_text(row)
    if prompt_text is None:
        return None

    condition = _text_or_none(row.get("condition")) or default_condition or "unspecified"
    return Stage5Example(
        example_id=_make_example_id(row, line_number=line_number),
        goal_index=_coerce_int(row.get("goal_index")),
        condition=condition,
        goal=_text_or_none(row.get("goal")),
        prompt_text=prompt_text,
        response_text=_find_response_text(row),
        is_success=_coerce_bool(row.get("is_success")),
        judge_score=_coerce_float(row.get("judge_score")),
        strongreject_score=_coerce_float(row.get("strongreject_score")),
        source_path=str(source_path),
        raw=row,
    )


def load_stage5_examples_with_metadata(
    path: str | Path,
    max_examples: int | None = None,
    default_condition: str | None = None,
) -> Stage5ExampleLoadResult:
    """Load normalized examples plus safe loader metadata."""

    if max_examples is not None and max_examples <= 0:
        raise ValueError("max_examples must be positive when provided.")

    input_path = validate_jsonl_path(path)
    examples: list[Stage5Example] = []
    skipped_contentless_rows = 0
    for line_number, row in enumerate(iter_jsonl(input_path), start=1):
        example = _normalize_example(
            row,
            line_number=line_number,
            source_path=input_path,
            default_condition=default_condition,
        )
        if example is None:
            skipped_contentless_rows += 1
            continue
        examples.append(example)
        if max_examples is not None and len(examples) >= max_examples:
            break

    return Stage5ExampleLoadResult(
        examples=examples,
        skipped_contentless_rows=skipped_contentless_rows,
        source_path=str(input_path),
    )


def load_stage5_examples(
    path: str | Path,
    max_examples: int | None = None,
    default_condition: str | None = None,
) -> list[Stage5Example]:
    """Load normalized Stage 5 examples without printing or writing contents."""

    return load_stage5_examples_with_metadata(
        path,
        max_examples=max_examples,
        default_condition=default_condition,
    ).examples


def _self_test() -> None:
    """Small internal smoke test; intentionally not run automatically."""

    import tempfile

    rows = [
        {
            "goal_index": "7",
            "goal": "goal text",
            "attack_prompt": "attack prompt",
            "target_response": "response",
            "is_success": "true",
            "judge_score": "10",
            "strongreject_score": "0.75",
        },
        {
            "id": "chat-1",
            "messages": [
                {"role": "system", "content": "be helpful"},
                {"role": "user", "content": "hello"},
            ],
            "response": "hi",
        },
        {"goal": "fallback prompt"},
        {"condition": "direct_harmful", "refusal_component": 1.23},
    ]
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".jsonl") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
        handle.flush()
        result = load_stage5_examples_with_metadata(handle.name)
        examples = load_stage5_examples(handle.name)

    assert result.num_examples == 3
    assert result.skipped_contentless_rows == 1
    assert len(examples) == 3
    assert result.examples[0].goal_index == 7
    assert result.examples[0].is_success is True
    assert result.examples[0].judge_score == 10.0
    assert result.examples[0].strongreject_score == 0.75
    assert result.examples[1].example_id == "chat-1"
    assert "user: hello" in result.examples[1].prompt_text
    assert result.examples[2].prompt_text == "fallback prompt"
