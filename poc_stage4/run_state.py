from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

from poc_stage4.schemas import make_json_safe


def log_progress(stage: str, message: str, *, enabled: bool = True, **fields: Any) -> None:
    if not enabled:
        return
    timestamp = datetime.now(timezone.utc).isoformat()
    suffix = ""
    if fields:
        suffix = " " + " ".join(f"{key}={make_json_safe(value)}" for key, value in fields.items())
    print(f"[{timestamp}] [{stage}] {message}{suffix}", file=sys.stderr, flush=True)


def progress_iter(
    iterable: Iterable[Any],
    *,
    total: int | None = None,
    desc: str,
    enabled: bool = True,
) -> Iterable[Any]:
    if not enabled:
        return iterable
    try:
        from tqdm.auto import tqdm

        return tqdm(iterable, total=total, desc=desc)
    except Exception:
        return iterable


def config_fingerprint(payload: dict[str, Any]) -> str:
    safe_payload = make_json_safe(payload)
    encoded = json.dumps(safe_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def atomic_write_json(path: str | Path, payload: dict[str, Any]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(make_json_safe(payload), handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    tmp_path.replace(output_path)


def append_jsonl(path: str | Path, row: dict[str, Any]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(make_json_safe(row), ensure_ascii=False) + "\n")
        handle.flush()


def read_jsonl_rows(path: str | Path) -> list[dict[str, Any]]:
    input_path = Path(path)
    if not input_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid checkpoint JSONL on line {line_number} in {input_path}: {exc}") from exc
    return rows


def row_key(row: dict[str, Any], fields: Sequence[str]) -> tuple[Any, ...]:
    return tuple(row.get(field) for field in fields)


def completed_rows_by_key(path: str | Path, key_fields: Sequence[str]) -> dict[tuple[Any, ...], dict[str, Any]]:
    rows = read_jsonl_rows(path)
    completed: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in rows:
        key = row_key(row, key_fields)
        if all(value is not None for value in key):
            completed[key] = row
    return completed


def write_checkpoint_manifest(
    checkpoint_dir: str | Path,
    *,
    stage: str,
    fingerprint_payload: dict[str, Any],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    checkpoint_path = Path(checkpoint_dir)
    checkpoint_path.mkdir(parents=True, exist_ok=True)
    manifest = {
        "stage": stage,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "config_fingerprint": config_fingerprint(fingerprint_payload),
        "fingerprint_payload": make_json_safe(fingerprint_payload),
        **(extra or {}),
    }
    atomic_write_json(checkpoint_path / "manifest.json", manifest)
    return manifest


def validate_checkpoint_manifest(
    checkpoint_dir: str | Path,
    *,
    stage: str,
    fingerprint_payload: dict[str, Any],
) -> dict[str, Any] | None:
    manifest_path = Path(checkpoint_dir) / "manifest.json"
    expected = config_fingerprint(fingerprint_payload)
    if not manifest_path.exists():
        return None
    with manifest_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    if manifest.get("stage") != stage:
        raise RuntimeError(
            f"Checkpoint manifest stage mismatch in {manifest_path}: "
            f"expected {stage!r}, found {manifest.get('stage')!r}."
        )
    actual = manifest.get("config_fingerprint")
    if actual != expected:
        raise RuntimeError(
            f"Checkpoint config mismatch in {manifest_path}. Refusing to resume with different settings. "
            f"Expected fingerprint {expected}, found {actual}."
        )
    return manifest
