from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from poc_stage2.hijacking_wrapper import run_hijacking_slice, summary_as_jsonable


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a small structured Chain-of-Thought Hijacking slice and write JSON artifacts."
    )
    parser.add_argument("--target-model", default="gpt-o4-mini")
    parser.add_argument("--start-example", type=int, default=1)
    parser.add_argument("--end-example", type=int, default=4)
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--n-iterations", type=int, default=2)
    parser.add_argument("--n-streams", type=int, default=6)
    parser.add_argument("--dataset", default="walledai/HarmBench")
    parser.add_argument("--dataset-split", default="standard")
    parser.add_argument("-v", "--verbosity", action="count", default=1)
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        result = run_hijacking_slice(
            target_model=args.target_model,
            start_example=args.start_example,
            end_example=args.end_example,
            n_iterations=args.n_iterations,
            n_streams=args.n_streams,
            dataset=args.dataset,
            dataset_split=args.dataset_split,
            verbosity=args.verbosity,
            wandb_mode="disabled",
        )
    except RuntimeError as exc:
        command = (
            f"py -3.12 -m poc_stage2.collect_hijacking_results "
            f"--target-model {args.target_model} "
            f"--start-example {args.start_example} "
            f"--end-example {args.end_example} "
            f"--output-dir {args.output_dir}"
        )
        print(str(exc), file=sys.stderr)
        print("Rerun after configuring credentials:", file=sys.stderr)
        print(command, file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path = output_dir / f"{result.output_stem}.jsonl"
    summary_path = output_dir / f"{result.output_stem}_summary.json"

    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in result.rows:
            handle.write(json.dumps(row.to_dict(), ensure_ascii=False) + "\n")

    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary_as_jsonable(result), handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print(f"Wrote row artifact: {jsonl_path}")
    print(f"Wrote summary artifact: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
