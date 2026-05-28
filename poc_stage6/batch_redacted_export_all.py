"""
Batch-run the Qwen token-trace exporter across all candidates.

Behavior:
- Loads candidates from the provided input JSONL (same format used by other scripts).
- For each example it will invoke the exporter as a subprocess with `--example-id` and
  `--redact-generation` to avoid storing plaintext generated outputs.
- If the per-example artifact already exists, it will be skipped (no overwrite).

Usage:
  python -m poc_stage6.batch_redacted_export_all --input-jsonl <path> --out-dir outputs/stage6/all_traces --model Qwen/Qwen3-14B --max-attempts 100

This script is conservative: it will not pass `--overwrite` to the exporter by default.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable

from poc_stage5.data_loading import load_stage5_examples_with_metadata, validate_jsonl_path


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(path.name + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    tmp_path.replace(path)


def _safe_filename_part(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_.-")
    return cleaned or "example"


def iter_examples(input_jsonl: Path) -> Iterable[dict]:
    loaded = load_stage5_examples_with_metadata(input_jsonl)
    for ex in loaded.examples:
        yield ex


def _load_artifact_summary(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        artifact = json.load(handle)
    return {
        "artifact_path": str(path),
        "example_id": artifact.get("selected_example", {}).get("example_id"),
        "qwen_run_success": artifact.get("qwen_run_success"),
        "prompt_token_count": len(artifact.get("prompt_token_ids") or []),
        "generation_token_count": len(artifact.get("generation_token_ids") or []),
        "token_table_length": len(artifact.get("token_table") or []),
        "generation_text_sha256": artifact.get("generation_text_sha256"),
        "generation_finish_reason": artifact.get("generation_finish_reason"),
        "thinking_segmentation_status": artifact.get("thinking_segmentation_status"),
        "token_table_reconstruction_status": artifact.get("token_table_reconstruction_status"),
        "artifact_version": artifact.get("artifact_version"),
        "search_status": artifact.get("search_summary", {}).get("search_status"),
    }


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    p = argparse.ArgumentParser(description="Batch run exporter for all examples with redaction and no-overwrite")
    p.add_argument("--input-jsonl", required=True)
    p.add_argument("--out-dir", default="outputs/stage6/all_traces")
    p.add_argument("--model", default="Qwen/Qwen3-14B")
    p.add_argument("--max-attempts", type=int, default=None)
    p.add_argument("--extra-args", default="", help="Extra args to pass to exporter (string).")
    p.add_argument("--summary-json", default=None, help="Where to write the final batch summary JSON. Defaults to <out-dir>/batch_summary.json")
    args = p.parse_args(argv)

    input_jsonl = validate_jsonl_path(args.input_jsonl)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = Path(args.summary_json) if args.summary_json else out_dir / "batch_summary.json"

    rows: list[dict] = []
    count = 0
    for ex in iter_examples(input_jsonl):
        count += 1
        if args.max_attempts is not None and count > args.max_attempts:
            print(f"Reached max attempts ({args.max_attempts}), stopping.")
            break

        example_id = ex.example_id
        slug = _safe_filename_part(example_id)
        output_path = out_dir / f"qwen3_14b_trace_{slug}.json"
        if output_path.exists():
            print(f"Skipping existing artifact: {output_path}")
            rows.append({
                "example_id": example_id,
                "artifact_path": str(output_path),
                "status": "skipped_existing",
                **_load_artifact_summary(output_path),
            })
            continue

        cmd = [
            sys.executable, "-m", "poc_stage6.export_qwen_token_trace",
            "--input-jsonl", str(input_jsonl),
            "--example-id", str(example_id),
            "--output-json", str(output_path),
            "--model-name-or-path", args.model,
            "--enable-thinking", "true",
            "--max-new-tokens", "768",
            "--redact-generation",
        ]

        # allow appending arbitrary extra args (e.g., --do-sample true)
        if args.extra_args:
            cmd.extend(args.extra_args.split())

        print("Running:", " ".join(cmd))
        try:
            res = subprocess.run(cmd, check=False)
            if res.returncode != 0:
                print(f"Exporter failed for {example_id} (rc={res.returncode}). See logs.")
                rows.append({
                    "example_id": example_id,
                    "artifact_path": str(output_path),
                    "status": "failed",
                    "returncode": res.returncode,
                })
            else:
                if output_path.exists():
                    rows.append({
                        "example_id": example_id,
                        "artifact_path": str(output_path),
                        "status": "completed",
                        **_load_artifact_summary(output_path),
                    })
        except Exception as exc:
            print(f"Exception while running exporter for {example_id}: {exc}")
            rows.append({
                "example_id": example_id,
                "artifact_path": str(output_path),
                "status": "exception",
                "error_message": str(exc),
            })

    summary = {
        "batch_version": "poc_stage6_batch_redacted_export_all_v1",
        "input_jsonl": str(input_jsonl),
        "out_dir": str(out_dir),
        "model": args.model,
        "max_attempts": args.max_attempts,
        "examples_seen": count,
        "completed_or_skipped": len(rows),
        "results": rows,
    }
    _atomic_write_json(summary_path, summary)
    print(f"Wrote batch summary: {summary_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
