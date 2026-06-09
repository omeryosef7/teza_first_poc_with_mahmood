"""
Stage 4.5B — Quality audit for LLM-generated onset annotations.

Reads the consensus_annotations.csv from a completed llm_annotate run,
computes quality metrics, checks the predefined quality gate, and writes:
  annotation_audit.json   (metrics + gate result)
  spotcheck_queue.csv     (examples needing spot-check)

Quality gate thresholds:
  parse_success_rate       >= 0.95
  provider_error_rate      <= 0.05
  two_pass_consensus_rate  >= 0.70
  median_agreement_distance <= 128 tokens

Usage:
  python -m poc_stage4_5.audit_llm_annotations --run-dir PATH
  python -m poc_stage4_5.audit_llm_annotations --consensus-csv PATH
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage4_5 import common

# ---------------------------------------------------------------------------
# Quality gate thresholds
# ---------------------------------------------------------------------------

GATE_PARSE_SUCCESS_MIN = 0.95
GATE_PROVIDER_ERROR_MAX = 0.05
GATE_CONSENSUS_RATE_MIN = 0.70
GATE_MEDIAN_DISTANCE_MAX = 128.0

SPOTCHECK_N_LOW_CONF = 3
SPOTCHECK_N_HIGH_CONF = 2

SPOTCHECK_CSV_FIELDS = [
    "example_id", "annotation_status", "confidence", "reason_category",
    "agreement_distance_tokens", "adjudication_used", "pass_1_status",
    "pass_2_status", "spotcheck_reason",
]


# ---------------------------------------------------------------------------
# Core audit logic
# ---------------------------------------------------------------------------

def audit_consensus_csv(rows: list[dict]) -> dict:
    """Compute quality metrics from consensus annotation rows."""
    n = len(rows)
    if n == 0:
        return {"n": 0, "error": "no_rows"}

    def _safe_float(v: str | None) -> float | None:
        if v is None or str(v).strip() == "":
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    def _safe_int(v: str | None) -> int | None:
        if v is None or str(v).strip() == "":
            return None
        try:
            return int(float(v))
        except (ValueError, TypeError):
            return None

    statuses = [r.get("annotation_status", "") for r in rows]
    n_annotated = sum(1 for s in statuses if s == "annotated")
    n_no_event = sum(1 for s in statuses if s == "no_harmful_interaction_found")
    n_uncertain = sum(1 for s in statuses if s == "uncertain")
    n_provider_error = sum(1 for s in statuses if s == "provider_error")
    n_invalid = sum(1 for s in statuses if s == "invalid_response")
    n_other = n - n_annotated - n_no_event - n_uncertain - n_provider_error - n_invalid

    # Parse success: any row that has a valid status (not provider_error or invalid)
    n_parse_success = n - n_provider_error - n_invalid
    parse_success_rate = n_parse_success / n if n > 0 else 0.0
    provider_error_rate = n_provider_error / n if n > 0 else 0.0

    # Two-pass consensus: annotated rows where adjudication_used == False
    # and both passes agreed (agreement_distance_tokens <= CONSENSUS_TOLERANCE)
    consensus_rows = [
        r for r in rows
        if r.get("annotation_status") == "annotated"
        and str(r.get("adjudication_used", "")).lower() not in ("true", "1")
    ]
    two_pass_consensus_rate = len(consensus_rows) / n_annotated if n_annotated > 0 else float("nan")

    # Agreement distances (annotated rows with a valid distance)
    distances = [
        _safe_float(r.get("agreement_distance_tokens"))
        for r in rows
        if r.get("annotation_status") == "annotated"
    ]
    distances = [d for d in distances if d is not None and math.isfinite(d)]
    if distances:
        distances_sorted = sorted(distances)
        mid = len(distances_sorted) // 2
        if len(distances_sorted) % 2 == 0:
            median_distance = (distances_sorted[mid - 1] + distances_sorted[mid]) / 2
        else:
            median_distance = float(distances_sorted[mid])
        mean_distance = sum(distances) / len(distances)
    else:
        median_distance = float("nan")
        mean_distance = float("nan")

    # Confidence stats (all rows)
    confidences = [
        _safe_float(r.get("confidence"))
        for r in rows
    ]
    confidences = [c for c in confidences if c is not None and math.isfinite(c)]
    mean_confidence = sum(confidences) / len(confidences) if confidences else float("nan")

    # Phase breakdown (annotated only)
    annotated_rows = [r for r in rows if r.get("annotation_status") == "annotated"]
    think_count = sum(1 for r in annotated_rows if r.get("onset_segment") == "think")
    final_count = sum(1 for r in annotated_rows if r.get("onset_segment") == "final")
    special_count = sum(1 for r in annotated_rows if r.get("onset_segment") == "special")
    none_count = sum(1 for r in annotated_rows if r.get("onset_segment") in ("none", ""))

    n_adjudication = sum(
        1 for r in rows
        if str(r.get("adjudication_used", "")).lower() in ("true", "1")
    )

    return {
        "n": n,
        "n_annotated": n_annotated,
        "n_no_event": n_no_event,
        "n_uncertain": n_uncertain,
        "n_provider_error": n_provider_error,
        "n_invalid": n_invalid,
        "n_other": n_other,
        "parse_success_rate": parse_success_rate,
        "annotation_rate": n_annotated / n,
        "no_event_rate": n_no_event / n,
        "uncertain_rate": n_uncertain / n,
        "provider_error_rate": provider_error_rate,
        "invalid_response_rate": n_invalid / n,
        "two_pass_consensus_rate": two_pass_consensus_rate,
        "median_agreement_distance": median_distance,
        "mean_agreement_distance": mean_distance,
        "mean_confidence": mean_confidence,
        "think_phase_event_count": think_count,
        "final_phase_event_count": final_count,
        "special_phase_event_count": special_count,
        "none_phase_count": none_count,
        "n_adjudication_used": n_adjudication,
    }


def check_quality_gate(metrics: dict) -> tuple[bool, list[str]]:
    """Return (passes, list_of_failures)."""
    failures = []

    psr = metrics.get("parse_success_rate", 0.0)
    if not isinstance(psr, float) or math.isnan(psr) or psr < GATE_PARSE_SUCCESS_MIN:
        failures.append(
            f"parse_success_rate={psr:.3f} < {GATE_PARSE_SUCCESS_MIN}"
        )

    per = metrics.get("provider_error_rate", 1.0)
    if not isinstance(per, float) or math.isnan(per) or per > GATE_PROVIDER_ERROR_MAX:
        failures.append(
            f"provider_error_rate={per:.3f} > {GATE_PROVIDER_ERROR_MAX}"
        )

    cr = metrics.get("two_pass_consensus_rate")
    if cr is None or (isinstance(cr, float) and math.isnan(cr)):
        failures.append("two_pass_consensus_rate=NaN (no annotated rows)")
    elif cr < GATE_CONSENSUS_RATE_MIN:
        failures.append(
            f"two_pass_consensus_rate={cr:.3f} < {GATE_CONSENSUS_RATE_MIN}"
        )

    md = metrics.get("median_agreement_distance")
    if md is None or (isinstance(md, float) and math.isnan(md)):
        # No annotated rows — treat as failure only if annotation_rate > 0
        if metrics.get("annotation_rate", 0) > 0:
            failures.append("median_agreement_distance=NaN for annotated rows")
    elif md > GATE_MEDIAN_DISTANCE_MAX:
        failures.append(
            f"median_agreement_distance={md:.1f} > {GATE_MEDIAN_DISTANCE_MAX}"
        )

    return len(failures) == 0, failures


def build_spotcheck_queue(rows: list[dict]) -> list[dict]:
    """Build a prioritized spotcheck queue."""
    spotcheck: list[dict] = []
    added_ids: set[str] = set()

    def _add(r: dict, reason: str) -> None:
        eid = r.get("example_id", "")
        if eid in added_ids:
            return
        added_ids.add(eid)
        spotcheck.append({
            "example_id": eid,
            "annotation_status": r.get("annotation_status"),
            "confidence": r.get("confidence"),
            "reason_category": r.get("reason_category"),
            "agreement_distance_tokens": r.get("agreement_distance_tokens"),
            "adjudication_used": r.get("adjudication_used"),
            "pass_1_status": r.get("pass_1_status"),
            "pass_2_status": r.get("pass_2_status"),
            "spotcheck_reason": reason,
        })

    # 1. All uncertain
    for r in rows:
        if r.get("annotation_status") == "uncertain":
            _add(r, "uncertain_annotation")

    # 2. All no-event
    for r in rows:
        if r.get("annotation_status") == "no_harmful_interaction_found":
            _add(r, "no_event_found")

    # 3. All disagreements > 64 tokens
    for r in rows:
        dist_str = r.get("agreement_distance_tokens", "")
        try:
            dist = float(dist_str) if dist_str else None
        except (ValueError, TypeError):
            dist = None
        if dist is not None and dist > 64:
            _add(r, f"disagreement_{int(dist)}_tokens")

    # 4. 3 lowest-confidence accepted annotations (deterministic: sort by confidence, take first 3)
    annotated = [r for r in rows if r.get("annotation_status") == "annotated"]

    def _conf(r: dict) -> float:
        try:
            return float(r.get("confidence", 1.0))
        except (ValueError, TypeError):
            return 1.0

    sorted_by_conf = sorted(annotated, key=_conf)
    for r in sorted_by_conf[:SPOTCHECK_N_LOW_CONF]:
        _add(r, "low_confidence_accepted")

    # 5. 2 high-confidence consensus (deterministic: sort by example_id, take last 2 from high end)
    high_conf = [r for r in annotated if _conf(r) >= 0.85 and
                 str(r.get("adjudication_used", "")).lower() not in ("true", "1")]
    high_conf_sorted = sorted(high_conf, key=lambda r: r.get("example_id", ""))
    # Take from the middle-high to be deterministic
    if high_conf_sorted:
        step = max(1, len(high_conf_sorted) // (SPOTCHECK_N_HIGH_CONF + 1))
        for i in range(SPOTCHECK_N_HIGH_CONF):
            idx = min((i + 1) * step, len(high_conf_sorted) - 1)
            _add(high_conf_sorted[idx], "high_confidence_consensus_sample")

    return spotcheck


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Audit LLM annotation quality and check quality gate.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    source = p.add_mutually_exclusive_group()
    source.add_argument(
        "--run-dir",
        type=Path,
        default=None,
        help="Run directory containing consensus_annotations.csv.",
    )
    source.add_argument(
        "--consensus-csv",
        type=Path,
        default=None,
        help="Direct path to consensus_annotations.csv.",
    )
    p.add_argument(
        "--no-write",
        action="store_true",
        default=False,
        help="Print results without writing output files.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.run_dir is not None:
        consensus_csv = args.run_dir / "consensus_annotations.csv"
        out_dir = args.run_dir
    elif args.consensus_csv is not None:
        consensus_csv = args.consensus_csv
        out_dir = consensus_csv.parent
    else:
        # Default: look for most recent run
        base = common.REPO_ROOT / "outputs" / "stage4_5" / "llm_harmful_interaction_annotations"
        if not base.exists():
            print("ERROR: no run directory found. Use --run-dir.", file=sys.stderr)
            return 1
        runs = sorted(base.iterdir())
        if not runs:
            print("ERROR: no runs found under", base, file=sys.stderr)
            return 1
        latest = runs[-1]
        consensus_csv = latest / "consensus_annotations.csv"
        out_dir = latest
        print(f"Using most recent run: {latest}")

    if not consensus_csv.exists():
        print(f"ERROR: consensus_annotations.csv not found: {consensus_csv}", file=sys.stderr)
        return 1

    rows = common.read_csv_as_list(consensus_csv)
    metrics = audit_consensus_csv(rows)
    passes_gate, failures = check_quality_gate(metrics)

    # Print summary
    print("\n=== LLM Annotation Quality Audit ===")
    print(f"  Total examples:             {metrics['n']}")
    print(f"  Annotated:                  {metrics['n_annotated']} ({metrics['annotation_rate']:.1%})")
    print(f"  No event found:             {metrics['n_no_event']} ({metrics['no_event_rate']:.1%})")
    print(f"  Uncertain:                  {metrics['n_uncertain']} ({metrics['uncertain_rate']:.1%})")
    print(f"  Provider errors:            {metrics['n_provider_error']} ({metrics['provider_error_rate']:.1%})")
    print(f"  Parse success rate:         {metrics['parse_success_rate']:.3f}  (gate: >= {GATE_PARSE_SUCCESS_MIN})")
    cr = metrics['two_pass_consensus_rate']
    cr_str = f"{cr:.3f}" if not (isinstance(cr, float) and (cr != cr)) else "NaN"
    print(f"  Two-pass consensus rate:    {cr_str}  (gate: >= {GATE_CONSENSUS_RATE_MIN})")
    md = metrics['median_agreement_distance']
    md_str = f"{md:.1f}" if not (isinstance(md, float) and (md != md)) else "NaN"
    print(f"  Median agreement distance:  {md_str} tokens  (gate: <= {GATE_MEDIAN_DISTANCE_MAX})")
    print(f"  Mean confidence:            {metrics['mean_confidence']:.3f}")
    print(f"  Onset phase (think/final/special): "
          f"{metrics['think_phase_event_count']} / "
          f"{metrics['final_phase_event_count']} / "
          f"{metrics['special_phase_event_count']}")
    print(f"  Adjudication used:          {metrics['n_adjudication_used']}")
    print()

    if passes_gate:
        print("QUALITY GATE: PASS")
    else:
        print("QUALITY GATE: FAIL")
        for f in failures:
            print(f"  FAILED: {f}")

    audit_result = {
        "metrics": metrics,
        "gate_passed": passes_gate,
        "gate_failures": failures,
        "gate_thresholds": {
            "parse_success_rate_min": GATE_PARSE_SUCCESS_MIN,
            "provider_error_rate_max": GATE_PROVIDER_ERROR_MAX,
            "two_pass_consensus_rate_min": GATE_CONSENSUS_RATE_MIN,
            "median_agreement_distance_max": GATE_MEDIAN_DISTANCE_MAX,
        },
        "source_csv": str(consensus_csv),
    }

    spotcheck = build_spotcheck_queue(rows)

    if not args.no_write:
        common.atomic_write_json(out_dir / "annotation_audit.json", common.make_json_safe(audit_result))
        print(f"\nWritten: annotation_audit.json")

        if spotcheck:
            common.write_csv(out_dir / "spotcheck_queue.csv", spotcheck, SPOTCHECK_CSV_FIELDS)
            print(f"Written: spotcheck_queue.csv ({len(spotcheck)} rows)")
        else:
            print("Spotcheck queue: empty (no rows needed spot-check).")

    return 0 if passes_gate else 1


if __name__ == "__main__":
    sys.exit(main())
