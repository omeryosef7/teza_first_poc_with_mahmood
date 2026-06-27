"""
Build condition-G manifest for Stage 4.8 (Qwen3 and Gemma4).

Condition G = bare harmful goal + thinking DISABLED.
  - Same user_message_text as condition D for each source_example_id
  - enable_thinking = False  (differs from D which has enable_thinking = True)
  - Same (source_example_id, seed) tuples that already exist for A/D/E/F

The manifest covers ONLY the tuples in g_condition_job_targets.jsonl —
i.e., tuples where A/D/E/F are all present but G is missing.
This ensures G is paired with existing conditions for the full factorial test.

Outputs:
  outputs/stage4_8/repeated_generation_manifest_cond_g_qwen3.jsonl
  outputs/stage4_8_gemma/repeated_generation_manifest_cond_g_gemma.jsonl
  outputs/stage4/factorial_balanced/manifest_cond_g_audit.json

Usage:
  python -m poc_stage4_8.build_manifest_condition_g
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_G_TARGETS = _REPO_ROOT / "outputs" / "stage4" / "factorial_balanced" / "g_condition_job_targets.jsonl"
_QWEN3_REP_PROMPTS = _REPO_ROOT / "outputs" / "stage4_7" / "replication_prompts.jsonl"
_GEMMA_REP_PROMPTS = _REPO_ROOT / "outputs" / "stage4_8_gemma" / "replication_prompts.jsonl"
_QWEN3_OUT = _REPO_ROOT / "outputs" / "stage4_8" / "repeated_generation_manifest_cond_g_qwen3.jsonl"
_GEMMA_OUT = _REPO_ROOT / "outputs" / "stage4_8_gemma" / "repeated_generation_manifest_cond_g_gemma.jsonl"
_AUDIT_OUT = _REPO_ROOT / "outputs" / "stage4" / "factorial_balanced" / "manifest_cond_g_audit.json"

_QWEN3_MODEL = "Qwen/Qwen3-14B"
_QWEN3_MODEL_REVISION = "40c069824f4251a91eefaf281ebe4c544efd3e18"
_GEMMA_MODEL = "google/gemma-3-4b-it"
_GEMMA_MODEL_FAMILY = "gemma4"
_QWEN3_MODEL_FAMILY = "qwen3"

_DO_SAMPLE = True
_TEMPERATURE = 0.7
_TOP_P = 0.95
_MAX_NEW_TOKENS = 32768
_CONDITION = "G"


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


def _build_d_message_map(rep_prompts_path: Path) -> dict[str, str]:
    """Build source_example_id → user_message_text for condition D."""
    rows = _load_jsonl(rep_prompts_path)
    d_map: dict[str, str] = {}
    for r in rows:
        if r.get("condition") != "D":
            continue
        sid = r.get("source_example_id", "")
        msg = r.get("user_message_text", "") or r.get("_user_message_text", "")
        if sid and msg:
            d_map[sid] = msg
    return d_map


def build_manifest(targets: list[dict], d_map: dict[str, str], model_family: str) -> tuple[list[dict], list[str]]:
    """Build manifest rows for condition G from the G targets list and D message map.

    Returns (rows, errors).
    """
    rows = []
    errors = []

    # Model-specific fields
    if model_family == _QWEN3_MODEL_FAMILY:
        model_name = _QWEN3_MODEL
        model_revision = _QWEN3_MODEL_REVISION
    else:
        model_name = _GEMMA_MODEL
        model_revision = None

    for t in targets:
        if t.get("model_family") != model_family:
            continue
        sid = t["source_example_id"]
        seed = t["seed"]
        goal_index = t.get("goal_index")

        user_message = d_map.get(sid, "")
        if not user_message:
            errors.append(f"No D condition message found for source_example_id={sid!r}")
            continue

        prompt_hash = _sha256(user_message)
        safe_sid = sid.replace("|", "__")
        run_id = f"{safe_sid}__cond_G__seed_{seed}"

        row = {
            "run_id": run_id,
            "source_example_id": sid,
            "goal_index": goal_index,
            "condition": _CONDITION,
            "seed": seed,
            "enable_thinking": False,  # Condition G: thinking OFF
            "model_family": model_family,
            "model_name_or_path": model_name,
            "do_sample": _DO_SAMPLE,
            "temperature": _TEMPERATURE,
            "top_p": _TOP_P,
            "max_new_tokens": _MAX_NEW_TOKENS,
            "prompt_hash": prompt_hash,
            "user_message_text": user_message,  # stored inline so no lookup needed at runtime
        }
        if model_revision:
            row["model_revision"] = model_revision
        rows.append(row)

    return rows, errors


def main() -> None:
    if not _G_TARGETS.exists():
        print(f"ERROR: G targets not found at {_G_TARGETS}")
        print("Run `python -m poc_stage4.build_complete_factorial_manifest` first.")
        sys.exit(1)

    targets = _load_jsonl(_G_TARGETS)
    print(f"Loaded {len(targets)} G-condition job targets")

    qwen3_targets = [t for t in targets if t.get("model_family") == _QWEN3_MODEL_FAMILY]
    gemma_targets = [t for t in targets if t.get("model_family") == _GEMMA_MODEL_FAMILY]
    print(f"  Qwen3: {len(qwen3_targets)} | Gemma4: {len(gemma_targets)}")

    all_errors = []

    # Qwen3 manifest
    if qwen3_targets:
        if not _QWEN3_REP_PROMPTS.exists():
            all_errors.append(f"Qwen3 replication prompts not found: {_QWEN3_REP_PROMPTS}")
        else:
            d_map_qwen3 = _build_d_message_map(_QWEN3_REP_PROMPTS)
            print(f"Qwen3 D messages loaded: {len(d_map_qwen3)}")
            qwen3_rows, errs = build_manifest(targets, d_map_qwen3, _QWEN3_MODEL_FAMILY)
            all_errors.extend(errs)
            _QWEN3_OUT.parent.mkdir(parents=True, exist_ok=True)
            with _QWEN3_OUT.open("w") as f:
                for r in qwen3_rows:
                    f.write(json.dumps(r) + "\n")
            print(f"Wrote {len(qwen3_rows)} Qwen3 G rows → {_QWEN3_OUT}")
    else:
        print("No Qwen3 G targets — skipping Qwen3 manifest")

    # Gemma4 manifest
    if gemma_targets:
        if not _GEMMA_REP_PROMPTS.exists():
            all_errors.append(f"Gemma4 replication prompts not found: {_GEMMA_REP_PROMPTS}")
        else:
            d_map_gemma = _build_d_message_map(_GEMMA_REP_PROMPTS)
            print(f"Gemma4 D messages loaded: {len(d_map_gemma)}")
            gemma_rows, errs = build_manifest(targets, d_map_gemma, _GEMMA_MODEL_FAMILY)
            all_errors.extend(errs)
            _GEMMA_OUT.parent.mkdir(parents=True, exist_ok=True)
            with _GEMMA_OUT.open("w") as f:
                for r in gemma_rows:
                    f.write(json.dumps(r) + "\n")
            print(f"Wrote {len(gemma_rows)} Gemma4 G rows → {_GEMMA_OUT}")
    else:
        print("No Gemma4 G targets — skipping Gemma4 manifest")

    # Audit
    audit = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "n_targets": len(targets),
        "n_qwen3_targets": len(qwen3_targets),
        "n_gemma_targets": len(gemma_targets),
        "errors": all_errors,
        "ok": len(all_errors) == 0,
    }
    _AUDIT_OUT.parent.mkdir(parents=True, exist_ok=True)
    with _AUDIT_OUT.open("w") as f:
        json.dump(audit, f, indent=2)
    print(f"Audit → {_AUDIT_OUT}")

    if all_errors:
        print("\nERRORS:")
        for e in all_errors:
            print(f"  {e}")
        sys.exit(1)
    else:
        print("\nAll G-condition manifests built successfully.")
        print("Next: submit smoke jobs:")
        print(f"  RUN_DIR=outputs/stage4_8/runs/run_cond_g_qwen3_smoke_$(date +%s) sbatch slurm_scripts/stage4_8_cond_g_qwen3.slurm")
        print(f"  RUN_DIR=outputs/stage4_8_gemma/runs/run_cond_g_gemma_smoke_$(date +%s) sbatch slurm_scripts/stage4_8_cond_g_gemma.slurm")


if __name__ == "__main__":
    main()
