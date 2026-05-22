from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from poc_stage5.data_loading import iter_jsonl, validate_jsonl_path

from poc_stage7.objectives import ObjectiveParameters, _atomic_write_json, summarize_objective_rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Aggregate Stage 7 objective-comparison JSONL rows into a summary JSON file."
    )
    parser.add_argument("--input-jsonl", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def validate_config(args: argparse.Namespace) -> tuple[Path, Path, bool]:
    return validate_jsonl_path(args.input_jsonl), Path(args.output_json), bool(args.overwrite)


def main() -> int:
    args = build_parser().parse_args()
    try:
        input_jsonl, output_json, overwrite = validate_config(args)
        if output_json.exists() and not overwrite:
            raise FileExistsError(f"Output file already exists. Use --overwrite to replace it: {output_json}")
        rows = list(iter_jsonl(input_jsonl))
        regions = sorted({str(row.get("region")) for row in rows if row.get("region") is not None})
        hidden_state_index = next((int(row["hidden_state_index"]) for row in rows if row.get("hidden_state_index") is not None), 40)
        first_row = rows[0] if rows else {}
        params = ObjectiveParameters(
            lambda_refusal=float(first_row.get("lambda_refusal", 1.0)),
            lambda_preserve=float(first_row.get("lambda_preserve", 1.0)),
            alpha=float(first_row.get("alpha", 1.0)),
            beta=float(first_row.get("beta", 1.0)),
            delta=float(first_row.get("delta", 1.0)),
        )
        summary = summarize_objective_rows(
            rows,
            regions=tuple(regions),
            hidden_state_index=hidden_state_index,
            params=params,
        )
        summary["input_jsonl"] = str(input_jsonl)
        summary["output_json"] = str(output_json)
        _atomic_write_json(output_json, summary)
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
