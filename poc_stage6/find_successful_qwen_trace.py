from __future__ import annotations

from poc_stage6.export_qwen_token_trace import build_parser, run_export, validate_config


def build_search_parser():
    parser = build_parser()
    parser.prog = "python -m poc_stage6.find_successful_qwen_trace"
    parser.description = (
        "Search hijacking candidates sequentially and stop at the first real successful Qwen/Qwen3-14B rerun. "
        "This wrapper preserves the single-example exporter while forcing search-until-success mode."
    )
    return parser


def main() -> None:
    parser = build_search_parser()
    args = parser.parse_args()
    if args.mode == "existing-only" or getattr(args, "existing_only", False):
        parser.error("The search wrapper only supports rerun mode, not existing-only.")
    args.search_until_success = True
    config = validate_config(args)
    if not config.search_until_success:
        parser.error("The search wrapper requires --search-until-success semantics.")
    run_export(config)


if __name__ == "__main__":
    main()
