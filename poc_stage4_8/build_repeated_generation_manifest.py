"""
Stage 4.8 — Build the 60-row generation manifest.

For each selected source prompt (4 prompts, 1 per goal):
  × conditions A, D, F (3 conditions)
  × seeds 101–105 (5 seeds)
  = 60 total rows

Reuses the prompt text directly from Stage 4.7's replication_prompts.jsonl
so no new prompt construction is needed.

Sampling config (pre-registered, never tuned after viewing results):
  do_sample=True, temperature=0.7, top_p=0.95, max_new_tokens=32768

Writes:
  outputs/stage4_8/repeated_generation_manifest.jsonl  (60 rows)
  outputs/stage4_8/manifest_audit.json

Usage:
  python -m poc_stage4_8.build_repeated_generation_manifest
      [--source-selection outputs/stage4_8/source_prompt_selection.csv]
      [--replication-prompts outputs/stage4_7/replication_prompts.jsonl]
      [--output-dir outputs/stage4_8]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_SOURCE_SELECTION = _REPO_ROOT / "outputs" / "stage4_8" / "source_prompt_selection.csv"
_REPLICATION_PROMPTS = _REPO_ROOT / "outputs" / "stage4_7" / "replication_prompts.jsonl"
_OUTPUT_DIR = _REPO_ROOT / "outputs" / "stage4_8"

_MODEL = "Qwen/Qwen3-14B"
_MODEL_REVISION = "40c069824f4251a91eefaf281ebe4c544efd3e18"
_SEEDS = [101, 102, 103, 104, 105]
_CONDITIONS = ["A", "D", "F"]
_DO_SAMPLE = True
_TEMPERATURE = 0.7
_TOP_P = 0.95
_MAX_NEW_TOKENS = 32768
_EXPECTED_TOTAL = 60  # 4 × 3 × 5


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_manifest(
    source_selection_path: Path,
    replication_prompts_path: Path,
) -> list[dict]:
    # Load selected source prompts
    with open(source_selection_path, encoding="utf-8") as f:
        selected = list(csv.DictReader(f))
    print(f"Loaded {len(selected)} selected source prompts")

    # Load replication prompts lookup
    rep_prompts = _load_jsonl(replication_prompts_path)
    # Key: (source_example_id, condition) → prompt row
    prompt_lookup: dict[tuple[str, str], dict] = {}
    for r in rep_prompts:
        key = (r["source_example_id"], r["condition"])
        prompt_lookup[key] = r

    manifest_rows: list[dict] = []

    for sel in selected:
        source_id = sel["source_example_id"]
        goal_idx = sel["goal_index"]

        for condition in _CONDITIONS:
            key = (source_id, condition)
            if key not in prompt_lookup:
                raise KeyError(
                    f"Condition {condition} for source {source_id} not found in "
                    f"replication_prompts.jsonl. "
                    f"Available keys for this source: "
                    f"{[k for k in prompt_lookup if k[0] == source_id]}"
                )
            prompt_row = prompt_lookup[key]
            user_message = prompt_row.get("user_message_text", "")
            prompt_hash = _sha256(user_message)

            for seed in _SEEDS:
                safe_source_id = source_id.replace("|", "__")
                run_id = f"{safe_source_id}__cond_{condition}__seed_{seed}"
                manifest_rows.append({
                    "run_id": run_id,
                    "source_example_id": source_id,
                    "goal_index": goal_idx,
                    "condition": condition,
                    "seed": seed,
                    "enable_thinking": condition in ("A", "D", "F"),
                    "model_name_or_path": _MODEL,
                    "model_revision": _MODEL_REVISION,
                    "do_sample": _DO_SAMPLE,
                    "temperature": _TEMPERATURE,
                    "top_p": _TOP_P,
                    "max_new_tokens": _MAX_NEW_TOKENS,
                    "prompt_hash": prompt_hash,
                    "source_prompt_sha256": prompt_row.get("source_prompt_sha256"),
                    "transformed_prompt_sha256": prompt_row.get("transformed_prompt_sha256"),
                    "source_prompt_tokens": prompt_row.get("source_prompt_tokens"),
                    "transformed_prompt_tokens": prompt_row.get("prompt_token_count"),
                    "transformation_method": prompt_row.get("transformation_method"),
                    "length_match_ratio": prompt_row.get("length_match_ratio"),
                    "selection_stratum": sel.get("selection_stratum"),
                    # user_message_text not stored here for safety — loaded from replication_prompts.jsonl at run time
                })

    return manifest_rows


def audit_manifest(rows: list[dict]) -> dict:
    errors = []
    warnings = []

    n = len(rows)
    if n != _EXPECTED_TOTAL:
        errors.append(f"Expected {_EXPECTED_TOTAL} rows, got {n}")

    # Unique run_ids
    run_ids = [r["run_id"] for r in rows]
    if len(run_ids) != len(set(run_ids)):
        errors.append("Duplicate run_ids in manifest")

    # Seeds present
    seeds_present = sorted(set(int(r["seed"]) for r in rows))
    if seeds_present != sorted(_SEEDS):
        errors.append(f"Seeds mismatch: {seeds_present} vs expected {sorted(_SEEDS)}")

    # Conditions present
    conds_present = sorted(set(r["condition"] for r in rows))
    if conds_present != sorted(_CONDITIONS):
        errors.append(f"Conditions mismatch: {conds_present}")

    # Goals: exactly 4 unique source prompts
    source_ids = sorted(set(r["source_example_id"] for r in rows))
    if len(source_ids) != 4:
        errors.append(f"Expected 4 unique source prompts, got {len(source_ids)}")
    goals = sorted(set(str(r["goal_index"]) for r in rows))
    if goals != [str(g) for g in sorted([0, 1, 2, 3])]:
        errors.append(f"Goals mismatch: {goals}")

    # Per-cell count: exactly 5 rows per (source, condition)
    from collections import Counter
    cell_counts = Counter((r["source_example_id"], r["condition"]) for r in rows)
    wrong_cells = {k: v for k, v in cell_counts.items() if v != len(_SEEDS)}
    if wrong_cells:
        errors.append(f"Wrong per-cell counts: {wrong_cells}")

    # Sampling config consistent
    for r in rows:
        if r.get("do_sample") != _DO_SAMPLE:
            errors.append(f"do_sample mismatch in run_id={r['run_id']}")
        if abs(float(r.get("temperature", 0)) - _TEMPERATURE) > 1e-6:
            errors.append(f"temperature mismatch in run_id={r['run_id']}")
        if abs(float(r.get("top_p", 0)) - _TOP_P) > 1e-6:
            errors.append(f"top_p mismatch in run_id={r['run_id']}")
        if int(r.get("max_new_tokens", 0)) != _MAX_NEW_TOKENS:
            errors.append(f"max_new_tokens mismatch in run_id={r['run_id']}")

    # run_id format includes seed
    for r in rows:
        seed = str(r["seed"])
        if f"__seed_{seed}" not in r["run_id"]:
            errors.append(f"run_id {r['run_id']} does not contain seed component __seed_{seed}")

    return {
        "passed": len(errors) == 0,
        "n_rows": n,
        "n_unique_sources": len(source_ids),
        "seeds": seeds_present,
        "conditions": conds_present,
        "errors": errors,
        "warnings": warnings,
        "sampling_config": {
            "do_sample": _DO_SAMPLE,
            "temperature": _TEMPERATURE,
            "top_p": _TOP_P,
            "max_new_tokens": _MAX_NEW_TOKENS,
        },
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build Stage 4.8 generation manifest.")
    p.add_argument("--source-selection", type=Path, default=_SOURCE_SELECTION)
    p.add_argument("--replication-prompts", type=Path, default=_REPLICATION_PROMPTS)
    p.add_argument("--output-dir", type=Path, default=_OUTPUT_DIR)
    args = p.parse_args(argv)

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Building manifest from {args.source_selection} ...")
    rows = build_manifest(args.source_selection, args.replication_prompts)
    print(f"  Built {len(rows)} manifest rows")

    # Assert exactly 60
    if len(rows) != _EXPECTED_TOTAL:
        print(f"ERROR: Expected {_EXPECTED_TOTAL} rows, got {len(rows)}")
        return 1

    # Audit
    audit = audit_manifest(rows)
    status = "PASSED" if audit["passed"] else "FAILED"
    print(f"Manifest audit: {status}")
    for e in audit.get("errors", []):
        print(f"  ERROR: {e}")

    # Write manifest
    manifest_path = out_dir / "repeated_generation_manifest.jsonl"
    with open(manifest_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, default=str) + "\n")
    print(f"Wrote {manifest_path} ({len(rows)} rows)")

    # Write audit JSON
    audit["created_utc"] = datetime.now(timezone.utc).isoformat()
    audit_path = out_dir / "manifest_audit.json"
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2)
    print(f"Wrote {audit_path}")

    print(f"\nManifest: {len(rows)} generations planned")
    print(f"  {len(set(r['source_example_id'] for r in rows))} source prompts × "
          f"{len(_CONDITIONS)} conditions × {len(_SEEDS)} seeds = {_EXPECTED_TOTAL}")
    print(f"  Sampling: do_sample={_DO_SAMPLE} temperature={_TEMPERATURE} "
          f"top_p={_TOP_P} max_new_tokens={_MAX_NEW_TOKENS}")

    return 0 if audit["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
