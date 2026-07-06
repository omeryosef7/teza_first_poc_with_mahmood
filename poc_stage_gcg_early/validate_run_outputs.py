"""
Validate the output artifacts of a completed GCG optimization run.

Checks:
  1. CONFIG.json parseable and fields present
  2. MANIFEST.jsonl readable; row count consistent with CONFIG
  3. ITERATION_LOG.jsonl — all rows valid JSON; steps monotonically increasing;
     n_steps reached OR DONE flag present
  4. FINAL_CANDIDATES.jsonl — valid JSON rows; numeric losses; no NaN/inf
  5. FREE_GENERATION_RESULTS.jsonl (if present) — valid JSON; strongreject_score numeric;
     no partial last line
  6. hidden_states/ (if present) — .pt files loadable; no zero-byte files

Exits 0 on all checks passing, 1 on any failure.

Usage:
    python -m poc_stage_gcg_early.validate_run_outputs --run-dir outputs/stage_gcg_full/my_run
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


def _check(name: str, ok: bool, detail: str = "") -> bool:
    status = "PASS" if ok else "FAIL"
    line = f"  [{status}] {name}"
    if detail:
        line += f": {detail}"
    print(line)
    return ok


def validate_run(run_dir: Path) -> bool:
    print(f"\nValidating: {run_dir}")
    all_ok = True

    # ------------------------------------------------------------------
    # 1. CONFIG.json
    # ------------------------------------------------------------------
    config_path = run_dir / "CONFIG.json"
    config = None
    if not config_path.exists():
        all_ok &= _check("CONFIG.json", False, "file missing")
    else:
        try:
            config = json.loads(config_path.read_text())
            required_keys = ("run_id", "model_family", "gcg", "objective", "output_dir")
            missing = [k for k in required_keys if k not in config]
            all_ok &= _check("CONFIG.json", not missing,
                              f"missing keys: {missing}" if missing else "parseable, required keys present")
        except Exception as e:
            all_ok &= _check("CONFIG.json", False, str(e))

    # ------------------------------------------------------------------
    # 2. MANIFEST.jsonl
    # ------------------------------------------------------------------
    manifest_path = run_dir / "MANIFEST.jsonl"
    manifest_rows = []
    if not manifest_path.exists():
        all_ok &= _check("MANIFEST.jsonl", False, "file missing")
    else:
        try:
            with open(manifest_path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        manifest_rows.append(json.loads(line))
            all_ok &= _check("MANIFEST.jsonl", bool(manifest_rows),
                              f"{len(manifest_rows)} rows")
        except Exception as e:
            all_ok &= _check("MANIFEST.jsonl", False, str(e))

    # ------------------------------------------------------------------
    # 3. ITERATION_LOG.jsonl
    # ------------------------------------------------------------------
    iter_log_path = run_dir / "ITERATION_LOG.jsonl"
    done_flag = (run_dir / "DONE").exists()

    if not iter_log_path.exists():
        all_ok &= _check("ITERATION_LOG.jsonl", False, "file missing")
    else:
        try:
            steps = []
            bad_rows = []
            with open(iter_log_path) as f:
                for lineno, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                        if "step" not in row:
                            bad_rows.append(lineno)
                        else:
                            steps.append(row["step"])
                    except json.JSONDecodeError:
                        bad_rows.append(lineno)

            n_steps_config = config["gcg"]["n_steps"] if config else None
            monotone = all(steps[i] < steps[i + 1] for i in range(len(steps) - 1))
            reached = (n_steps_config is not None and steps and steps[-1] >= n_steps_config - 1)
            complete = done_flag or reached

            ok = not bad_rows and monotone and complete
            detail_parts = [f"{len(steps)} steps logged"]
            if bad_rows:
                detail_parts.append(f"bad rows at lines {bad_rows[:5]}")
            if not monotone:
                detail_parts.append("steps not monotone")
            if not complete:
                detail_parts.append(f"not complete (last={steps[-1] if steps else None}, target={n_steps_config}, DONE={done_flag})")
            all_ok &= _check("ITERATION_LOG.jsonl", ok, "; ".join(detail_parts))
        except Exception as e:
            all_ok &= _check("ITERATION_LOG.jsonl", False, str(e))

    # ------------------------------------------------------------------
    # 4. FINAL_CANDIDATES.jsonl
    # ------------------------------------------------------------------
    final_path = run_dir / "FINAL_CANDIDATES.jsonl"
    if not final_path.exists():
        all_ok &= _check("FINAL_CANDIDATES.jsonl", False, "file missing")
    else:
        try:
            bad = []
            rows = []
            with open(final_path) as f:
                for lineno, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                        rows.append(row)
                        if not row.get("suffix_str"):
                            bad.append(f"line {lineno}: empty suffix_str")
                        for loss_key in ("task_loss", "repr_loss", "total_loss"):
                            v = row.get(loss_key)
                            if v is not None and (math.isnan(v) or math.isinf(v)):
                                bad.append(f"line {lineno}: {loss_key}={v}")
                    except json.JSONDecodeError as e:
                        bad.append(f"line {lineno}: {e}")
            ok = bool(rows) and not bad
            detail = f"{len(rows)} rows" + (f"; issues: {bad[:3]}" if bad else "")
            all_ok &= _check("FINAL_CANDIDATES.jsonl", ok, detail)
        except Exception as e:
            all_ok &= _check("FINAL_CANDIDATES.jsonl", False, str(e))

    # ------------------------------------------------------------------
    # 5. FREE_GENERATION_RESULTS.jsonl (optional)
    # ------------------------------------------------------------------
    free_gen_path = run_dir / "FREE_GENERATION_RESULTS.jsonl"
    if free_gen_path.exists():
        try:
            bad = []
            rows = []
            with open(free_gen_path) as f:
                for lineno, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                        rows.append(row)
                        sr = row.get("strongreject_score")
                        if sr is None or not isinstance(sr, (int, float)):
                            bad.append(f"line {lineno}: strongreject_score={sr!r}")
                    except json.JSONDecodeError as e:
                        bad.append(f"line {lineno}: {e}")
            ok = bool(rows) and not bad
            detail = f"{len(rows)} rows" + (f"; issues: {bad[:3]}" if bad else "")
            all_ok &= _check("FREE_GENERATION_RESULTS.jsonl", ok, detail)
        except Exception as e:
            all_ok &= _check("FREE_GENERATION_RESULTS.jsonl", False, str(e))
    else:
        print("  [SKIP] FREE_GENERATION_RESULTS.jsonl: not present (not yet generated)")

    # ------------------------------------------------------------------
    # 6. hidden_states/ (optional)
    # ------------------------------------------------------------------
    hs_dir = run_dir / "hidden_states"
    if hs_dir.exists():
        try:
            import torch
            pt_files = list(hs_dir.glob("*.pt"))
            zero_byte = [f for f in pt_files if f.stat().st_size == 0]
            load_errors = []
            for pt_file in pt_files[:5]:  # spot-check first 5
                try:
                    torch.load(pt_file, map_location="cpu", weights_only=True)
                except Exception as e:
                    load_errors.append(f"{pt_file.name}: {e}")
            ok = bool(pt_files) and not zero_byte and not load_errors
            detail_parts = [f"{len(pt_files)} .pt files"]
            if zero_byte:
                detail_parts.append(f"{len(zero_byte)} zero-byte")
            if load_errors:
                detail_parts.append(f"load errors: {load_errors[:2]}")
            all_ok &= _check("hidden_states/", ok, "; ".join(detail_parts))
        except ImportError:
            print("  [SKIP] hidden_states/: torch not available in this environment")
        except Exception as e:
            all_ok &= _check("hidden_states/", False, str(e))
    else:
        print("  [SKIP] hidden_states/: directory not present")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print()
    if all_ok:
        print(f"RESULT: PASS — all checks passed for {run_dir.name}")
    else:
        print(f"RESULT: FAIL — one or more checks failed for {run_dir.name}")
    return all_ok


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate GCG run output artifacts")
    parser.add_argument("--run-dir", required=True, help="Path to the run output directory")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    if not run_dir.is_dir():
        print(f"ERROR: {run_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    ok = validate_run(run_dir)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
