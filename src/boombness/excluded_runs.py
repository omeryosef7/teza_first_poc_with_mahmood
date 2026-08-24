#!/usr/bin/env python
"""Machine-readable manifest of run directories that MUST NOT be ingested (plan §2.2).

Why this file exists
--------------------
`RunDir.finish()` is the only thing that blesses a run: it writes metadata.json, summary.json and
DONE.json. A run that died before finish() leaves behind a directory that still LOOKS like a result
-- config.json, RUNMETA.json, a plots/ dir, and, in the dangerous case, a full-sized results payload
that no one ever validated. `common.require_done` is the consumer-side guard for ONE directory, but
any glob-based analysis (`glob("outputs/boombness/<exp>/*/")`) enumerates directories BEFORE anything
gets a chance to call it, and a scan that merely counts or averages files never calls it at all.

This module makes the exclusion list an artifact instead of a habit: scan the tree once, write
EXCLUDED_RUNS.json, and let consumers ask `is_excluded(run_dir)` / `filter_run_dirs(dirs)`.

NOTHING HERE DELETES. The skeleton directories are the evidence of a debugging sequence (three
xb10rev8 attempts in nineteen minutes, two xb8 attempts forty-seven seconds apart); their existence
and their timestamps are data about how the sprint ran. `safe_to_delete` is emitted as False for
every row, on purpose.

Usage
-----
    python -m src.boombness.excluded_runs --write        # regenerate the manifest
    python -m src.boombness.excluded_runs                # dry run, print the report

    from src.boombness.excluded_runs import is_excluded, filter_run_dirs
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import subprocess
import sys
from typing import Any, Dict, Iterable, List, Optional

SCHEMA = "EXCLUDED_RUNS/1"

#: reasons a run dir may carry. `superseded` is part of the vocabulary for rows whose only defect is
#: that a later run replaced them; the on-disk reasons below take precedence when both apply, and the
#: supersession is then carried by the `superseded_by` field instead.
REASONS = ("no_done_json", "aborted", "empty_skeleton", "superseded")

#: files written by the run harness itself (common.RunDir). Anything else in a run dir is payload.
BOOKKEEPING_FILES = frozenset({
    "config.json", "RUNMETA.json", "metadata.json", "summary.json",
    "DONE.json", "ABORTED.json", "DONE.json.retracted_by_abort",
})

#: experiment subdirectories of outputs/boombness/ that hold per-run directories.
DEFAULT_EXPERIMENTS = (
    "crossbank_knockout_test", "score_behavior", "judge", "extract_boombness",
    "retrieval_strength", "rederive_crossbank", "tokenization_audit",
)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_OUTPUTS_ROOT = os.path.join(REPO_ROOT, "outputs", "boombness")
DEFAULT_MANIFEST = os.path.join(DEFAULT_OUTPUTS_ROOT, "EXCLUDED_RUNS.json")


# --------------------------------------------------------------------------- #
# scanning
# --------------------------------------------------------------------------- #
def parse_run_id(run_id: str) -> Dict[str, Optional[str]]:
    """Split the house run_id convention `<tag>_<YYYYmmdd>_<HHMMSS>_<pid>`.

    Returns {"tag": ..., "stamp": "YYYYmmdd_HHMMSS" or None, "pid": ...}. Tags may themselves contain
    underscores (`ctrl_rand_s20260820`), so the split is from the RIGHT and validated by shape; a
    run_id that does not match the convention yields tag=run_id and stamp=None, which makes it
    unmatchable for supersession rather than wrongly matched.
    """
    parts = run_id.rsplit("_", 2)
    if len(parts) == 3:
        tag, date, rest = parts
        time_pid = rest.split("_")
        if len(date) == 8 and date.isdigit() and len(time_pid[0]) == 6 and time_pid[0].isdigit():
            return {"tag": tag, "stamp": f"{date}_{time_pid[0]}", "pid": time_pid[0]}
    parts2 = run_id.split("_")
    for i in range(len(parts2) - 2):
        if len(parts2[i]) == 8 and parts2[i].isdigit() and len(parts2[i + 1]) == 6 and parts2[i + 1].isdigit():
            return {"tag": "_".join(parts2[:i]), "stamp": f"{parts2[i]}_{parts2[i + 1]}",
                    "pid": "_".join(parts2[i + 2:]) or None}
    return {"tag": run_id, "stamp": None, "pid": None}


def _payload_files(run_dir: str) -> List[str]:
    """Non-bookkeeping, non-empty files under run_dir (recursive), relative to run_dir."""
    out = []
    for dirpath, _dirnames, filenames in os.walk(run_dir):
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, run_dir)
            if rel in BOOKKEEPING_FILES:
                continue
            try:
                if os.path.getsize(full) == 0:
                    continue
            except OSError:
                continue
            out.append(rel)
    return sorted(out)


def _describe(run_dir: str) -> str:
    """Human-readable inventory of what is actually on disk, with sizes. READ-ONLY."""
    bits = []
    for name in sorted(os.listdir(run_dir)):
        full = os.path.join(run_dir, name)
        if os.path.isdir(full):
            try:
                n = len(os.listdir(full))
            except OSError:
                n = -1
            bits.append(f"{name}/ ({n} files)")
        else:
            try:
                bits.append(f"{name} ({os.path.getsize(full)} B)")
            except OSError:
                bits.append(name)
    return ", ".join(bits) if bits else "(empty directory)"


def classify_run(run_dir: str) -> Optional[Dict[str, Any]]:
    """Classify ONE run directory. Returns None for a run that finished cleanly (not excluded).

    Precedence: ABORTED.json wins (the run announced its own death, which is more informative than
    "no DONE"), then an absence of any payload (`empty_skeleton`), then plain `no_done_json` -- the
    dangerous shape, a directory holding a plausible full-sized results file that finish() never
    blessed.
    """
    has_done = os.path.exists(os.path.join(run_dir, "DONE.json"))
    has_aborted = os.path.exists(os.path.join(run_dir, "ABORTED.json"))
    if has_done and not has_aborted:
        return None
    payload = _payload_files(run_dir)
    if has_aborted:
        reason = "aborted"
    elif not payload:
        reason = "empty_skeleton"
    else:
        reason = "no_done_json"
    run_id = os.path.basename(os.path.normpath(run_dir))
    return {
        "run_dir": os.path.relpath(os.path.abspath(run_dir), REPO_ROOT),
        "run_id": run_id,
        "experiment": os.path.basename(os.path.dirname(os.path.abspath(run_dir))),
        "reason": reason,
        "detail": _describe(run_dir),
        "has_partial_results": bool(payload),
        "superseded_by": None,       # filled in by scan_experiment
        "safe_to_delete": False,     # ALWAYS false: these dirs are evidence, not garbage
    }


def scan_experiment(exp_dir: str) -> Dict[str, Any]:
    """Scan one experiment dir. Returns {"n_dirs", "n_missing_done", "rows"}. READ-ONLY."""
    if not os.path.isdir(exp_dir):
        return {"n_dirs": 0, "n_missing_done": 0, "rows": []}
    run_dirs = sorted(d for d in os.listdir(exp_dir) if os.path.isdir(os.path.join(exp_dir, d)))
    rows: List[Dict[str, Any]] = []
    completed: List[Dict[str, Optional[str]]] = []
    n_missing_done = 0
    for name in run_dirs:
        full = os.path.join(exp_dir, name)
        if not os.path.exists(os.path.join(full, "DONE.json")):
            n_missing_done += 1
        row = classify_run(full)
        if row is None:
            info = parse_run_id(name)
            completed.append({"run_id": name, "tag": info["tag"], "stamp": info["stamp"]})
        else:
            rows.append(row)
    for row in rows:
        row["superseded_by"] = _find_successor(row["run_id"], completed)
    return {"n_dirs": len(run_dirs), "n_missing_done": n_missing_done, "rows": rows}


def _find_successor(run_id: str, completed: Iterable[Dict[str, Optional[str]]]) -> Optional[str]:
    """Nearest LATER completed run sharing the tag prefix, or None when it cannot be established.

    Deliberately conservative: no stamp on either side, or no same-tag completed run later in time,
    means None. A guess here would be worse than silence -- `superseded_by` is the field a reader
    would use to decide which directory the real number came from.
    """
    info = parse_run_id(run_id)
    if info["stamp"] is None:
        return None
    best = None
    for cand in completed:
        if cand["tag"] != info["tag"] or cand["stamp"] is None:
            continue
        if cand["stamp"] <= info["stamp"]:
            continue
        if best is None or cand["stamp"] < best["stamp"]:
            best = cand
    return best["run_id"] if best else None


def _git_commit() -> Optional[str]:
    try:
        return subprocess.check_output(
            ["git", "-C", REPO_ROOT, "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return None


def build_manifest(outputs_root: str = DEFAULT_OUTPUTS_ROOT,
                   experiments: Iterable[str] = DEFAULT_EXPERIMENTS) -> Dict[str, Any]:
    """Build the manifest payload. Pure read: touches nothing on disk."""
    runs: List[Dict[str, Any]] = []
    per_exp: Dict[str, Dict[str, int]] = {}
    for exp in experiments:
        res = scan_experiment(os.path.join(outputs_root, exp))
        per_exp[exp] = {"n_dirs": res["n_dirs"], "n_missing_done": res["n_missing_done"],
                        "n_excluded": len(res["rows"])}
        runs.extend(res["rows"])
    runs.sort(key=lambda r: (r["experiment"], r["run_id"]))
    return {
        "schema": SCHEMA,
        "written_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "written_by_commit": _git_commit(),
        "outputs_root": os.path.relpath(os.path.abspath(outputs_root), REPO_ROOT),
        "experiments_scanned": list(experiments),
        "per_experiment": per_exp,
        "n_excluded": len(runs),
        "runs": runs,
    }


def validate_manifest(manifest: Dict[str, Any]) -> None:
    """Raise ValueError if the payload does not match EXCLUDED_RUNS/1."""
    if manifest.get("schema") != SCHEMA:
        raise ValueError(f"schema is {manifest.get('schema')!r}, expected {SCHEMA!r}")
    for key in ("written_at", "written_by_commit", "runs"):
        if key not in manifest:
            raise ValueError(f"manifest missing required key {key!r}")
    if not isinstance(manifest["runs"], list):
        raise ValueError("runs must be a list")
    for row in manifest["runs"]:
        for key in ("run_dir", "run_id", "experiment", "reason", "detail",
                    "has_partial_results", "superseded_by", "safe_to_delete"):
            if key not in row:
                raise ValueError(f"run row {row.get('run_id')!r} missing key {key!r}")
        if row["reason"] not in REASONS:
            raise ValueError(f"run row {row['run_id']!r} has reason {row['reason']!r} "
                             f"outside {REASONS}")
        if not isinstance(row["has_partial_results"], bool):
            raise ValueError(f"run row {row['run_id']!r}: has_partial_results must be bool")
        if row["safe_to_delete"] is not False:
            raise ValueError(f"run row {row['run_id']!r}: safe_to_delete must be False "
                             f"-- this manifest never authorises deletion")
        if row["superseded_by"] is not None and not isinstance(row["superseded_by"], str):
            raise ValueError(f"run row {row['run_id']!r}: superseded_by must be str or null")


def write_manifest(manifest: Dict[str, Any], path: str = DEFAULT_MANIFEST) -> str:
    validate_manifest(manifest)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    return path


# --------------------------------------------------------------------------- #
# loader (the consumer side)
# --------------------------------------------------------------------------- #
_CACHE: Dict[str, Dict[str, Any]] = {}


def load_manifest(path: str = DEFAULT_MANIFEST, use_cache: bool = True) -> Dict[str, Any]:
    """Load and validate the manifest. A missing file yields an empty (but valid) manifest."""
    key = os.path.abspath(path)
    if use_cache and key in _CACHE:
        return _CACHE[key]
    if not os.path.exists(path):
        manifest = {"schema": SCHEMA, "written_at": None, "written_by_commit": None, "runs": []}
    else:
        with open(path) as f:
            manifest = json.load(f)
        validate_manifest(manifest)
    if use_cache:
        _CACHE[key] = manifest
    return manifest


def excluded_run_dirs(path: str = DEFAULT_MANIFEST) -> set:
    """Set of ABSOLUTE, normalised run dirs named by the manifest."""
    out = set()
    for row in load_manifest(path).get("runs", []):
        rd = row["run_dir"]
        if not os.path.isabs(rd):
            rd = os.path.join(REPO_ROOT, rd)
        out.add(os.path.normpath(os.path.abspath(rd)))
    return out


def is_excluded(run_dir: str, path: str = DEFAULT_MANIFEST) -> bool:
    """True when `run_dir` is on the exclusion manifest. Accepts absolute or repo-relative paths."""
    rd = run_dir if os.path.isabs(run_dir) else os.path.join(REPO_ROOT, run_dir)
    return os.path.normpath(os.path.abspath(rd)) in excluded_run_dirs(path)


def filter_run_dirs(run_dirs: Iterable[str], path: str = DEFAULT_MANIFEST) -> List[str]:
    """Drop every excluded dir from `run_dirs`, preserving order. The glob-safe entry point."""
    bad = excluded_run_dirs(path)
    keep = []
    for d in run_dirs:
        rd = d if os.path.isabs(d) else os.path.join(REPO_ROOT, d)
        if os.path.normpath(os.path.abspath(rd)) not in bad:
            keep.append(d)
    return keep


# --------------------------------------------------------------------------- #
def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--outputs-root", default=DEFAULT_OUTPUTS_ROOT)
    ap.add_argument("--out", default=DEFAULT_MANIFEST)
    ap.add_argument("--experiments", nargs="*", default=list(DEFAULT_EXPERIMENTS))
    ap.add_argument("--write", action="store_true", help="write the manifest (default: dry run)")
    args = ap.parse_args(argv)

    manifest = build_manifest(args.outputs_root, args.experiments)
    validate_manifest(manifest)
    print(f"[excluded_runs] scanned {args.outputs_root}")
    for exp, c in manifest["per_experiment"].items():
        print(f"  {exp:<26s} dirs={c['n_dirs']:<4d} missing_DONE={c['n_missing_done']:<4d} "
              f"excluded={c['n_excluded']}")
    by_reason: Dict[str, int] = {}
    for row in manifest["runs"]:
        by_reason[row["reason"]] = by_reason.get(row["reason"], 0) + 1
    print(f"  TOTAL excluded={manifest['n_excluded']} by_reason={by_reason}")
    print(f"  with partial results on disk (the dangerous shape) = "
          f"{sum(1 for r in manifest['runs'] if r['has_partial_results'] and r['reason'] == 'no_done_json')}")
    if args.write:
        print(f"[excluded_runs] wrote {write_manifest(manifest, args.out)}")
    else:
        print("[excluded_runs] dry run; pass --write to emit the manifest. NOTHING IS EVER DELETED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
