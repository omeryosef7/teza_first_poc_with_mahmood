"""
Safe inspector for Qwen token-trace artifacts and search_summary.json.

Usage examples:
  python -m poc_stage6.inspect_qwen_artifact outputs/.../search_summary.json
  python -m poc_stage6.inspect_qwen_artifact outputs/.../qwen3_14b_success_trace_....json

This prints only compact, supervisor-safe summary fields (no raw transcripts).
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from typing import Any, Dict


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def summarize_artifact(artifact: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "qwen_run_success": artifact.get("qwen_run_success"),
        "prompt_token_count": len(artifact.get("prompt_token_ids", [])),
        "generation_token_count": len(artifact.get("generation_token_ids", [])),
        "token_table_length": len(artifact.get("token_table", [])),
        "generation_finish_reason": artifact.get("generation_finish_reason"),
        "thinking_segmentation_status": artifact.get("thinking_segmentation_status"),
        "token_table_reconstruction_status": artifact.get("token_table_reconstruction_status"),
        "prompt_roundtrip": artifact.get("prompt_roundtrip_saved") or artifact.get("prompt_roundtrip_exact") or artifact.get("prompt_roundtrip"),
        "generation_roundtrip_saved": artifact.get("generation_roundtrip_saved"),
    }


def summarize_search_summary(s: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "search_status": s.get("search_status"),
        "qwen_run_success": s.get("qwen_run_success"),
        "attempts": s.get("attempts"),
        "output_artifact_path": s.get("output_artifact_path"),
        "created_utc": s.get("created_utc"),
    }


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    p = argparse.ArgumentParser(prog="inspect_qwen_artifact", description="Summarize Qwen token-trace artifacts safely")
    p.add_argument("path", help="Path to an artifact JSON or a search_summary.json")
    p.add_argument("--json", action="store_true", help="Output summary as JSON")
    args = p.parse_args(argv)

    path = args.path
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return 2

    try:
        data = load_json(path)
    except Exception as e:
        print(f"Failed to load JSON from {path}: {e}")
        return 3

    out: Dict[str, Any] = {}

    # If this looks like a search_summary, show its summary and then try to load the artifact it points to.
    if isinstance(data, dict) and data.get("output_artifact_path"):
        out["search_summary"] = summarize_search_summary(data)
        artifact_path = data.get("output_artifact_path")
        if artifact_path and os.path.exists(artifact_path):
            try:
                art = load_json(artifact_path)
                out["artifact_summary"] = summarize_artifact(art)
            except Exception as e:
                out["artifact_error"] = f"failed to load artifact {artifact_path}: {e}"
        else:
            out["artifact_error"] = f"artifact path not found locally: {artifact_path}"

    # If the file itself looks like a token-trace artifact, summarize it directly.
    elif isinstance(data, dict) and ("token_table" in data or "generation_token_ids" in data or "prompt_token_ids" in data):
        out["artifact_summary"] = summarize_artifact(data)

    else:
        out["info"] = "Unrecognized JSON schema. Provide a search_summary.json or a token-trace artifact."

    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        for k, v in out.items():
            print(f"{k}:")
            if isinstance(v, dict):
                for kk, vv in v.items():
                    print(f"  {kk}: {vv}")
            else:
                print(f"  {v}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
