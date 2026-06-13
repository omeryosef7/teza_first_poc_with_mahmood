#!/usr/bin/env python3
"""
Task 0 — Repository / artifact audit.

Walks all canonical artifact paths, checks existence, counts rows/files,
extracts CSV headers, and flags warnings.

Usage:
    python -m poc_meeting.mahmood_48h_update.build_artifact_inventory \
        --output-dir outputs/meeting/mahmood_48h_update_<TIMESTAMP>
"""

import argparse
import csv
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stderr)
log = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


CANONICAL_ARTIFACTS = [
    {
        "name": "stage4_token_dynamics",
        "path": "outputs/stage4/token_dynamics/full_20260604_101929",
        "type": "dir",
        "is_canonical": True,
        "note": "Frozen Stage 4 token dynamics; 11GB; read-only",
    },
    {
        "name": "stage4_analysis_dataset",
        "path": "outputs/stage4/token_dynamics/full_20260604_101929/analysis/analysis_dataset.csv",
        "type": "csv",
        "is_canonical": True,
    },
    {
        "name": "stage4_6_full_run",
        "path": "outputs/stage4_6/runs_output_full_20260610_091021",
        "type": "dir",
        "is_canonical": True,
        "note": "Stage 4.6 controlled ablation, conditions A/B/C/D/E",
    },
    {
        "name": "stage4_6_condition_summary",
        "path": "outputs/stage4_6/runs_output_full_20260610_091021/analysis/condition_summary.csv",
        "type": "csv",
        "is_canonical": True,
    },
    {
        "name": "stage4_6_per_run_results",
        "path": "outputs/stage4_6/runs_output_full_20260610_091021/analysis/canonical_per_run_results.csv",
        "type": "csv",
        "is_canonical": True,
        "fallback": "outputs/stage4_6/runs_output_full_20260610_091021/analysis/per_run_results.csv",
    },
    {
        "name": "stage4_7_full_run",
        "path": "outputs/stage4_7/runs/run_array_20260610_1442",
        "type": "dir",
        "is_canonical": True,
        "note": "Stage 4.7 replication, conditions A/D/F/E, 12 prompts × 4 = 48 runs",
    },
    {
        "name": "stage4_7_condition_summary",
        "path": "outputs/stage4_7/runs/run_array_20260610_1442/analysis/condition_summary.csv",
        "type": "csv",
        "is_canonical": True,
    },
    {
        "name": "stage4_7_canonical_per_run",
        "path": "outputs/stage4_7/runs/run_array_20260610_1442/analysis/canonical_per_run_results.csv",
        "type": "csv",
        "is_canonical": True,
    },
    {
        "name": "stage4_7_paired_contrasts",
        "path": "outputs/stage4_7/runs/run_array_20260610_1442/analysis/paired_contrasts.csv",
        "type": "csv",
        "is_canonical": True,
    },
    {
        "name": "stage4_7_goal_stratified",
        "path": "outputs/stage4_7/runs/run_array_20260610_1442/analysis/goal_stratified_summary.csv",
        "type": "csv",
        "is_canonical": True,
    },
    {
        "name": "stage4_7_replication_prompts",
        "path": "outputs/stage4_7/replication_prompts.jsonl",
        "type": "jsonl",
        "is_canonical": True,
    },
    {
        "name": "stage4_8_full_run",
        "path": "outputs/stage4_8/runs/run_array_20260611_0109",
        "type": "dir",
        "is_canonical": True,
        "note": "Stage 4.8 stochastic replication, conditions A/D/F, 4 prompts × 5 seeds = 60 gens",
    },
    {
        "name": "stage4_8_condition_summary",
        "path": "outputs/stage4_8/runs/run_array_20260611_0109/analysis/condition_summary.csv",
        "type": "csv",
        "is_canonical": True,
    },
    {
        "name": "stage4_8_cell_summary",
        "path": "outputs/stage4_8/runs/run_array_20260611_0109/analysis/cell_summary.csv",
        "type": "csv",
        "is_canonical": True,
    },
    {
        "name": "stage4_8_matched_cells",
        "path": "outputs/stage4_8/runs/run_array_20260611_0109/analysis/matched_outcome_cells.csv",
        "type": "csv",
        "is_canonical": True,
    },
    {
        "name": "stage4_8_manifest",
        "path": "outputs/stage4_8/repeated_generation_manifest.jsonl",
        "type": "jsonl",
        "is_canonical": True,
    },
    {
        "name": "stage6_traces_full",
        "path": "outputs/stage6/all_traces_full",
        "type": "dir",
        "is_canonical": True,
        "note": "Stage 6 full token traces, 43 JSON files",
    },
    {
        "name": "prior_meeting_package",
        "path": "outputs/meeting/mahmood_20260611",
        "type": "dir",
        "is_canonical": True,
        "note": "Previous meeting package, 73/73 passed audit",
    },
    {
        "name": "prior_one_page_brief",
        "path": "outputs/meeting/mahmood_20260611/docs/ONE_PAGE_ADVISOR_BRIEF.md",
        "type": "file",
        "is_canonical": True,
        "note": "Located in outputs/meeting/ not docs/ root",
    },
    {
        "name": "docs_sprint_results",
        "path": "docs/STAGE4_CURRENT_SPRINT_RESULTS.md",
        "type": "file",
        "is_canonical": True,
    },
    {
        "name": "docs_mahmood_brief",
        "path": "docs/MAHMOOD_NEXT_MEETING_BRIEF.md",
        "type": "file",
        "is_canonical": True,
    },
    {
        "name": "docs_qa_prep",
        "path": "docs/Q&A_PREPARATION.md",
        "type": "file",
        "is_canonical": False,
        "note": "MISSING — not yet written; will be created in 48h package",
    },
    {
        "name": "project_summary",
        "path": "PROJECT_SUMMARY_MAY25_JUN11.md",
        "type": "file",
        "is_canonical": True,
    },
]


def _count_csv_rows(p: Path) -> tuple[int, list[str]]:
    try:
        with open(p, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            return len(rows), list(reader.fieldnames or [])
    except Exception as e:
        return -1, [f"error: {e}"]


def _count_jsonl_rows(p: Path) -> int:
    try:
        return sum(1 for line in open(p) if line.strip())
    except Exception:
        return -1


def _count_dir_files(p: Path) -> int:
    return len(list(p.rglob("*")))


def _file_size_mb(p: Path) -> float:
    return p.stat().st_size / (1024 * 1024)


def audit_artifact(spec: dict) -> dict:
    rel = spec["path"]
    full = _REPO_ROOT / rel
    artifact_type = spec.get("type", "file")

    entry: dict = {
        "name": spec["name"],
        "path": rel,
        "type": artifact_type,
        "exists": False,
        "n_files_or_rows": None,
        "key_columns": [],
        "is_canonical": spec.get("is_canonical", False),
        "size_mb": None,
        "warnings": [],
        "note": spec.get("note", ""),
    }

    # Try primary path, then fallback
    target = full
    if not target.exists() and "fallback" in spec:
        fallback = _REPO_ROOT / spec["fallback"]
        if fallback.exists():
            entry["warnings"].append(f"primary not found; using fallback {spec['fallback']}")
            target = fallback
            entry["path"] = spec["fallback"]

    if not target.exists():
        entry["warnings"].append("path does not exist")
        # Search for alternatives
        parent = target.parent
        if parent.exists():
            alts = sorted(parent.glob(target.name.replace("canonical_", "").replace("_corrected", "") + "*"))
            if alts:
                entry["warnings"].append(f"alternatives found: {[str(a.name) for a in alts[:3]]}")
        return entry

    entry["exists"] = True

    if artifact_type == "csv":
        entry["size_mb"] = round(_file_size_mb(target), 3)
        n, cols = _count_csv_rows(target)
        entry["n_files_or_rows"] = n
        entry["key_columns"] = cols[:20]  # cap at 20 for readability
        if n == 0:
            entry["warnings"].append("CSV is empty (0 rows)")

    elif artifact_type == "jsonl":
        entry["size_mb"] = round(_file_size_mb(target), 3)
        n = _count_jsonl_rows(target)
        entry["n_files_or_rows"] = n
        if n == 0:
            entry["warnings"].append("JSONL is empty")

    elif artifact_type == "dir":
        n = _count_dir_files(target)
        entry["n_files_or_rows"] = n
        # compute rough size
        total_bytes = sum(f.stat().st_size for f in target.rglob("*") if f.is_file())
        entry["size_mb"] = round(total_bytes / (1024 * 1024), 1)
        if n == 0:
            entry["warnings"].append("directory is empty")

    elif artifact_type == "file":
        entry["size_mb"] = round(_file_size_mb(target), 3)
        if target.stat().st_size == 0:
            entry["warnings"].append("file is empty (0 bytes)")
        entry["n_files_or_rows"] = 1

    return entry


def _status(entry: dict) -> str:
    if not entry["exists"]:
        return "MISSING"
    if entry["warnings"]:
        return "WARN"
    return "PASS"


def write_markdown(entries: list[dict], out_path: Path) -> None:
    lines = [
        "# Artifact Inventory",
        f"\nGenerated: {datetime.utcnow().isoformat()}Z",
        "",
        "| Status | Name | Path | Type | Rows/Files | Size MB | Notes |",
        "|--------|------|------|------|-----------|---------|-------|",
    ]
    for e in entries:
        st = _status(e)
        icon = {"PASS": "✅", "WARN": "⚠️", "MISSING": "❌"}[st]
        notes = "; ".join(e["warnings"]) or e.get("note", "")
        n = e["n_files_or_rows"] if e["n_files_or_rows"] is not None else "—"
        sz = e["size_mb"] if e["size_mb"] is not None else "—"
        lines.append(
            f"| {icon} {st} | {e['name']} | `{e['path']}` | {e['type']} | {n} | {sz} | {notes} |"
        )

    # Summary
    n_pass = sum(1 for e in entries if _status(e) == "PASS")
    n_warn = sum(1 for e in entries if _status(e) == "WARN")
    n_miss = sum(1 for e in entries if _status(e) == "MISSING")
    lines += [
        "",
        f"**Summary:** {n_pass} PASS | {n_warn} WARN | {n_miss} MISSING",
        "",
        "## Condition Labels",
        "",
        "| Condition | Description |",
        "|-----------|-------------|",
        "| A | Full puzzle + thinking on |",
        "| B | ~50% puzzle + thinking on (Stage 4.6 only) |",
        "| C | ~25% puzzle + thinking on (Stage 4.6 only) |",
        "| D | Bare target + thinking on (no puzzle) |",
        "| E | Full puzzle + thinking off |",
        "| F | Length-matched benign wrapper + thinking on (Stage 4.7/4.8) |",
        "",
        "## Primary Success Metric",
        "",
        "`sr_success = strongreject_score >= 0.5` (complete-case; censored rows excluded)",
    ]

    out_path.write_text("\n".join(lines))
    log.info("Wrote %s", out_path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (created if missing). Default: auto-stamped outputs/meeting/mahmood_48h_update_<ts>",
    )
    args = parser.parse_args(argv)

    if args.output_dir is None:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        args.output_dir = _REPO_ROOT / f"outputs/meeting/mahmood_48h_update_{ts}"

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    log.info("Output dir: %s", out)

    log.info("Auditing %d canonical artifacts...", len(CANONICAL_ARTIFACTS))
    entries = [audit_artifact(spec) for spec in CANONICAL_ARTIFACTS]

    # Write JSON
    json_path = out / "artifact_inventory.json"
    json_path.write_text(json.dumps(entries, indent=2))
    log.info("Wrote %s", json_path)

    # Write Markdown
    write_markdown(entries, out / "artifact_inventory.md")

    # Print summary
    n_pass = sum(1 for e in entries if _status(e) == "PASS")
    n_warn = sum(1 for e in entries if _status(e) == "WARN")
    n_miss = sum(1 for e in entries if _status(e) == "MISSING")
    log.info("Audit complete: %d PASS  %d WARN  %d MISSING", n_pass, n_warn, n_miss)

    for e in entries:
        st = _status(e)
        if st != "PASS":
            log.warning("%-8s %s — %s", st, e["name"], "; ".join(e["warnings"]))

    return 0


if __name__ == "__main__":
    sys.exit(main())
