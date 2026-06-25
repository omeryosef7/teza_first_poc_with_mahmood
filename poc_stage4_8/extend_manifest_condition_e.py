"""
Stage 4.8 — Build 20-row condition-E manifest extension.

Condition E = full puzzle wrapper + thinking DISABLED.
Uses the same 4 source prompts as the main Stage 4.8 run.
Reuses condition-E prompt text already built in Stage 4.7 replication_prompts.jsonl.

Output:
  outputs/stage4_8/repeated_generation_manifest_cond_e.jsonl  (20 rows: 4 × 5 seeds)
  outputs/stage4_8/manifest_cond_e_audit.json

Usage:
  python -m poc_stage4_8.extend_manifest_condition_e
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
_CONDITION = "E"
_DO_SAMPLE = True
_TEMPERATURE = 0.7
_TOP_P = 0.95
_MAX_NEW_TOKENS = 32768
_EXPECTED_TOTAL = 20  # 4 × 5


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_manifest(
    source_selection_path: Path,
    replication_prompts_path: Path,
) -> list[dict]:
    with open(source_selection_path, encoding="utf-8") as f:
        selected = list(csv.DictReader(f))
    print(f"Loaded {len(selected)} selected source prompts")

    rep_prompts = _load_jsonl(replication_prompts_path)
    prompt_lookup: dict[tuple[str, str], dict] = {}
    for r in rep_prompts:
        key = (r["source_example_id"], r["condition"])
        prompt_lookup[key] = r

    manifest_rows: list[dict] = []

    for sel in selected:
        source_id = sel["source_example_id"]
        goal_idx = sel["goal_index"]

        key = (source_id, _CONDITION)
        if key not in prompt_lookup:
            raise KeyError(
                f"Condition {_CONDITION} for source {source_id} not found in "
                f"{replication_prompts_path}. "
                f"Available keys for this source: "
                f"{[k for k in prompt_lookup if k[0] == source_id]}"
            )
        prompt_row = prompt_lookup[key]
        # Get the user message — stored under _user_message_text or user_message_text
        user_message = prompt_row.get("user_message_text", "") or prompt_row.get("_user_message_text", "")
        if not user_message:
            raise ValueError(f"Empty user_message for {source_id} cond={_CONDITION}")

        prompt_hash = _sha256(user_message)

        for seed in _SEEDS:
            safe_source_id = source_id.replace("|", "__")
            run_id = f"{safe_source_id}__cond_{_CONDITION}__seed_{seed}"
            manifest_rows.append({
                "run_id": run_id,
                "source_example_id": source_id,
                "goal_index": goal_idx,
                "condition": _CONDITION,
                "seed": seed,
                "enable_thinking": False,  # Condition E: thinking disabled
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
                "transformed_prompt_tokens": prompt_row.get("transformed_prompt_tokens"),
                "transformation_method": prompt_row.get("transformation_method"),
                "length_match_ratio": prompt_row.get("length_match_ratio"),
                "selection_stratum": sel.get("selection_stratum"),
            })

    return manifest_rows


def audit_manifest(rows: list[dict]) -> dict:
    errors = []
    n = len(rows)
    if n != _EXPECTED_TOTAL:
        errors.append(f"Expected {_EXPECTED_TOTAL} rows, got {n}")

    run_ids = [r["run_id"] for r in rows]
    if len(run_ids) != len(set(run_ids)):
        errors.append("Duplicate run_ids")

    for r in rows:
        if r["condition"] != _CONDITION:
            errors.append(f"Wrong condition in row {r['run_id']}: {r['condition']}")
        if r.get("enable_thinking") is not False:
            errors.append(f"enable_thinking should be False in {r['run_id']}, got {r.get('enable_thinking')}")

    seeds_present = sorted(set(int(r["seed"]) for r in rows))
    if seeds_present != sorted(_SEEDS):
        errors.append(f"Seeds mismatch: {seeds_present} vs {sorted(_SEEDS)}")

    goals = sorted(set(str(r.get("goal_index", "")) for r in rows))
    if goals != ["0", "1", "2", "3"]:
        errors.append(f"Goals mismatch: {goals}")

    return {"n_rows": n, "errors": errors, "warnings": [], "ok": len(errors) == 0}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build condition-E manifest for Stage 4.8")
    parser.add_argument("--source-selection", default=str(_SOURCE_SELECTION))
    parser.add_argument("--replication-prompts", default=str(_REPLICATION_PROMPTS))
    parser.add_argument("--output-dir", default=str(_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "repeated_generation_manifest_cond_e.jsonl"
    audit_path = output_dir / "manifest_cond_e_audit.json"

    rows = build_manifest(
        source_selection_path=Path(args.source_selection),
        replication_prompts_path=Path(args.replication_prompts),
    )

    audit = audit_manifest(rows)
    if not audit["ok"]:
        print("AUDIT ERRORS:")
        for e in audit["errors"]:
            print(f"  {e}")
        sys.exit(1)

    with open(manifest_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    audit["manifest_path"] = str(manifest_path)
    audit["created_utc"] = datetime.now(timezone.utc).isoformat()
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2)

    print(f"Wrote {len(rows)} rows to {manifest_path}")
    print(f"Audit: {audit}")


if __name__ == "__main__":
    main()
