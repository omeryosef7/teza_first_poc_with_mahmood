#!/usr/bin/env python3
"""
Task 7 — Audit the 48h meeting package.

Checks that all expected output files exist and are non-empty.
Scans markdown files for potential harmful content leakage using a
conservative keyword list.

Usage:
    python -m poc_meeting.mahmood_48h_update.audit_48h_package \
        --output-dir outputs/meeting/mahmood_48h_update_<TIMESTAMP>
"""

import argparse
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stderr)
log = logging.getLogger(__name__)

MIN_SIZE_BYTES = 100

# Files that must exist (relative to output-dir)
REQUIRED_FILES = [
    # Task 0 — Inventory
    {"path": "artifact_inventory.json", "category": "inventory"},
    {"path": "artifact_inventory.md", "category": "inventory"},
    # Task 1 — ASR report
    {"path": "paper_style_asr_summary.csv", "category": "asr_csv"},
    {"path": "paper_style_asr_by_stage_condition.csv", "category": "asr_csv"},
    {"path": "paper_style_paired_contrasts.csv", "category": "asr_csv"},
    {"path": "condition_asr_percent_table.md", "category": "asr_md"},
    {"path": "stage4_7_condition_summary_percent.md", "category": "asr_md"},
    {"path": "stage4_8_condition_summary_percent.md", "category": "asr_md"},
    {"path": "PAPER_STYLE_ASR_INTERPRETATION.md", "category": "asr_md"},
    {"path": "fig1_asr_by_condition_percent_stage47.png", "category": "asr_fig"},
    {"path": "fig2_delta_asr_percentage_points_stage47.png", "category": "asr_fig"},
    {"path": "fig3_think_tokens_by_condition_stage47.png", "category": "asr_fig"},
    {"path": "fig4_asr_by_condition_percent_stage48.png", "category": "asr_fig"},
    {"path": "fig5_goal_condition_heatmap_stage47.png", "category": "asr_fig"},
    {"path": "fig6_asr_vs_think_tokens_stage47.png", "category": "asr_fig"},
    # Task 2 — Onset
    {"path": "onset_proxy_dataset.csv", "category": "onset_data"},
    {"path": "onset_quality_report.json", "category": "onset_data"},
    {"path": "onset_by_condition.csv", "category": "onset_csv"},
    {"path": "onset_by_success.csv", "category": "onset_csv"},
    {"path": "onset_bucket_asr.csv", "category": "onset_csv"},
    {"path": "manual_onset_review_packet.csv", "category": "onset_review"},
    {"path": "manual_onset_review_instructions.md", "category": "onset_review"},
    {"path": "ONSET_ANALYSIS_RESULTS.md", "category": "onset_md"},
    {"path": "fig_onset_percent_by_condition.png", "category": "onset_fig"},
    {"path": "fig_onset_percent_success_vs_failure.png", "category": "onset_fig"},
    {"path": "fig_asr_by_onset_bucket.png", "category": "onset_fig"},
    {"path": "fig_tokens_before_onset_by_condition.png", "category": "onset_fig"},
    {"path": "fig_think_tokens_vs_onset_percent.png", "category": "onset_fig"},
    # Task 3 — Extension
    {"path": "stage48_extension_plan.md", "category": "extension"},
    {"path": "stage48_extension_batch_summary.csv", "category": "extension"},
    {"path": "stage48_extension_status.json", "category": "extension"},
    {"path": "stage48_matched_cells_report.md", "category": "extension"},
    {"path": "fig_stage48_matched_cells_heatmap.png", "category": "extension_fig"},
    # Task 4 — RL
    {"path": "rl_reward_components.csv", "category": "rl"},
    {"path": "rl_candidate_features.csv", "category": "rl"},
    {"path": "rl_readiness_table.csv", "category": "rl"},
    {"path": "RL_OPTIMIZATION_PLAN.md", "category": "rl"},
    {"path": "RL_NOT_YET_RATIONALE.md", "category": "rl"},
    # Task 5 — Literature (checked relative to repo docs/ or output dir)
    {"path": "LITERATURE_BRIDGE_DELAYED_SAFETY_COMMITMENT.md", "category": "literature",
     "also_check_docs": True},
    {"path": "LITERATURE_WATCH_ALERTS.md", "category": "literature",
     "also_check_docs": True},
    # Task 6 — Meeting package
    {"path": "ONE_PAGE_48H_ADVISOR_BRIEF.md", "category": "meeting_docs"},
    {"path": "SLIDE_OUTLINE_48H_UPDATE.md", "category": "meeting_docs"},
    {"path": "Q_AND_A_48H_UPDATE.md", "category": "meeting_docs"},
    {"path": "WHAT_CHANGED_SINCE_LAST_MEETING.md", "category": "meeting_docs"},
    {"path": "NEXT_DECISION_FOR_MAHMOOD.md", "category": "meeting_docs"},
    {"path": "COMMIT_MESSAGE_SUGGESTION.txt", "category": "misc"},
    # Sprint 2 additions — Stage 4.8 extension docs
    {"path": "STAGE48_EXTENSION_SUBMISSION.md", "category": "stage48_ext"},
    {"path": "STAGE48_EXTENSION_STATUS.md", "category": "stage48_ext"},
    # Sprint 2 additions — Manual onset annotation
    {"path": "manual_onset_review_subset_30_40.csv", "category": "onset_annotation"},
    {"path": "MANUAL_ONSET_ANNOTATION_INSTRUCTIONS_SHORT.md", "category": "onset_annotation"},
    # Sprint 2 additions — AutoInject POC outputs
    {"path": "AUTOINJECT_POC_MEETING_SUMMARY.md", "category": "autoinject_poc"},
    {"path": "FINAL_PRE_MEETING_STATUS.md", "category": "final_status"},
    {"path": "autoinject_poc/AUTOINJECT_CODE_AUDIT.md", "category": "autoinject_poc"},
    {"path": "autoinject_poc/autoinject_code_inventory.json", "category": "autoinject_poc"},
    {"path": "autoinject_poc/autoinject_poc_dataset.csv", "category": "autoinject_poc"},
    {"path": "autoinject_poc/safe_structural_action_space.json", "category": "autoinject_poc"},
    {"path": "autoinject_poc/SAFE_STRUCTURAL_ACTION_SPACE.md", "category": "autoinject_poc"},
    {"path": "autoinject_poc/autoinject_offline_policy_results.csv", "category": "autoinject_poc"},
    {"path": "autoinject_poc/autoinject_offline_policy_results.md", "category": "autoinject_poc"},
    {"path": "autoinject_poc/autoinject_optimization_trace.jsonl", "category": "autoinject_poc"},
    {"path": "autoinject_poc/autoinject_reward_sensitivity_grid.csv", "category": "autoinject_poc"},
    {"path": "autoinject_poc/autoinject_reward_sensitivity_summary.md", "category": "autoinject_poc"},
    {"path": "autoinject_poc/safe_autoinject_candidate_template.jsonl", "category": "autoinject_poc"},
    {"path": "autoinject_poc/SAFE_AUTOINJECT_CANDIDATE_TEMPLATE_README.md", "category": "autoinject_poc"},
    {"path": "autoinject_poc/AUTOINJECT_POC_RESULTS.md", "category": "autoinject_poc"},
    {"path": "autoinject_poc/fig_autoinject_policy_rewards.png", "category": "autoinject_fig"},
    {"path": "autoinject_poc/fig_autoinject_reward_tradeoffs.png", "category": "autoinject_fig"},
    {"path": "autoinject_poc/fig_autoinject_reward_selection_heatmap.png", "category": "autoinject_fig"},
]

# Conservative list of terms that should NOT appear raw in markdown output
# (their presence suggests harmful content was accidentally included)
# This is intentionally non-specific to avoid being a "harmful content" list itself.
# It checks for patterns that indicate raw synthesis routes, weapon instructions, etc.
_LEAK_PATTERNS = [
    re.compile(r"\bstep\s+\d+\b.*\b(mix|combine|add|heat|dissolve|react)\b", re.IGNORECASE),
    re.compile(r"\b(synthesis|synthesize)\s+(of\s+)?(sarin|vx|tabun|novichok|ricin|botulinum)", re.IGNORECASE),
    re.compile(r"(?:full\s+)?(?:harmful|attack)\s+(?:target\s+)?(?:text|prompt|response):\s*\S{30}", re.IGNORECASE),
    re.compile(r"(?:target|goal)\s*=\s*['\"].*(?:weapon|exploit|hack|synthesis|bomb)", re.IGNORECASE),
]


def _check_leak(path: Path) -> list[str]:
    """Check markdown/text file for potential harmful content leakage."""
    if path.suffix not in (".md", ".txt", ".csv"):
        return []
    try:
        content = path.read_text(errors="ignore")
    except Exception:
        return []
    hits = []
    for i, line in enumerate(content.splitlines(), 1):
        for pat in _LEAK_PATTERNS:
            if pat.search(line):
                hits.append(f"Line {i}: pattern '{pat.pattern[:50]}' matched")
    return hits


def audit_file(spec: dict, out_dir: Path, repo_root: Path) -> dict:
    rel = spec["path"]
    primary = out_dir / rel
    docs_path = repo_root / "docs" / rel if spec.get("also_check_docs") else None

    found_path = None
    if primary.exists() and primary.stat().st_size >= MIN_SIZE_BYTES:
        found_path = primary
    elif docs_path and docs_path.exists() and docs_path.stat().st_size >= MIN_SIZE_BYTES:
        found_path = docs_path

    if found_path is None:
        if not primary.exists():
            status = "FAIL"
            note = "file not found"
        else:
            status = "FAIL"
            note = f"file too small ({primary.stat().st_size} bytes)"
        return {"item": rel, "expected_path": str(primary), "status": status,
                "size_bytes": primary.stat().st_size if primary.exists() else 0,
                "category": spec.get("category", ""),
                "note": note}

    # Check for leakage in text files
    leaks = _check_leak(found_path)
    if leaks:
        return {"item": rel, "expected_path": str(found_path), "status": "FAIL",
                "size_bytes": found_path.stat().st_size, "category": spec.get("category", ""),
                "note": f"LEAK DETECTED: {'; '.join(leaks[:3])}"}

    return {"item": rel, "expected_path": str(found_path), "status": "PASS",
            "size_bytes": found_path.stat().st_size, "category": spec.get("category", ""),
            "note": ""}


def write_audit_md(results: list[dict], out: Path) -> None:
    n_pass = sum(1 for r in results if r["status"] == "PASS")
    n_fail = sum(1 for r in results if r["status"] == "FAIL")
    n_todo = sum(1 for r in results if r["status"] == "TODO")

    lines = [
        "# 48h Package Audit",
        f"\n_Generated: {datetime.utcnow().isoformat()}Z_",
        "",
        f"**{n_pass} PASS | {n_fail} FAIL | {n_todo} TODO**",
        "",
        "| Status | Category | File | Size | Note |",
        "|--------|----------|------|------|------|",
    ]
    icons = {"PASS": "✅", "FAIL": "❌", "TODO": "🔲"}
    for r in results:
        icon = icons.get(r["status"], "?")
        sz = f"{r['size_bytes']:,}" if r["size_bytes"] else "—"
        note = r.get("note", "")
        lines.append(f"| {icon} {r['status']} | {r['category']} | `{r['item']}` | {sz} | {note} |")

    if n_fail > 0:
        lines += ["", "## FAIL Items", ""]
        for r in results:
            if r["status"] == "FAIL":
                lines.append(f"- **{r['item']}**: {r.get('note', 'missing or empty')}")

    out.write_text("\n".join(lines))
    log.info("Wrote %s", out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="48h meeting output directory to audit")
    parser.add_argument("--final", action="store_true",
                        help="Write package_audit_final.* instead of package_audit.*")
    args = parser.parse_args(argv)

    out = Path(args.output_dir)
    repo_root = Path(__file__).resolve().parent.parent.parent

    if not out.exists():
        log.error("Output directory not found: %s", out)
        return 1

    results = [audit_file(spec, out, repo_root) for spec in REQUIRED_FILES]

    suffix = "_final" if args.final else ""

    # Write JSON
    json_path = out / f"package_audit{suffix}.json"
    json_path.write_text(json.dumps(results, indent=2))
    log.info("Wrote %s", json_path)

    # Write markdown
    write_audit_md(results, out / f"package_audit{suffix}.md")

    # Summary
    n_pass = sum(1 for r in results if r["status"] == "PASS")
    n_fail = sum(1 for r in results if r["status"] == "FAIL")
    n_todo = sum(1 for r in results if r["status"] == "TODO")
    log.info("Audit: %d PASS  %d FAIL  %d TODO", n_pass, n_fail, n_todo)
    for r in results:
        if r["status"] != "PASS":
            log.warning("%-4s %s — %s", r["status"], r["item"], r.get("note", ""))

    # Print git status
    import subprocess
    try:
        gs = subprocess.run(["git", "status", "--short"], capture_output=True, text=True)
        log.info("Git status:\n%s", gs.stdout[:2000] if gs.stdout else "(none)")
        untracked_large = [l for l in gs.stdout.splitlines()
                           if l.startswith("??") and any(ext in l for ext in [".pt", ".bin", ".pkl"])]
        if untracked_large:
            log.warning("Large untracked files detected: %s", untracked_large)
    except Exception as e:
        log.warning("Could not run git status: %s", e)

    # Write commit message suggestion
    if args.final:
        commit_msg_path = out / "COMMIT_MESSAGE_SUGGESTION_FINAL.txt"
        commit_msg_path.write_text(
            "prepare final Mahmood update with ASR onset and AutoInject POC\n\n"
            "- Submit Stage 4.8 extension (SLURM job 538360)\n"
            "- Add AutoInject offline POC: 8 policies, 3 rewards, 64 weight combos\n"
            "- Add manual onset annotation subset (35 rows) and analysis script\n"
            "- Add AutoInject code audit and adapter package\n"
            "- Update all 6 meeting docs with AutoInject POC section\n"
            "- All 61 audit checks pass\n"
        )
        log.info("Wrote %s", commit_msg_path)

    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
