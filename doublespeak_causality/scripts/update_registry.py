#!/usr/bin/env python
"""update_registry.py — upsert one EXPERIMENT_REGISTRY.csv row per run dir.

Plan §2.2 item 7. `EXPERIMENT_REGISTRY.csv` stops at 2026-07-30; ~120 later runs,
including every headline result, have no row. This walks `outputs/*/` and adds the
missing ones, taking every value from `RUNMETA.json` when it exists and otherwise
reconstructing it in memory with `backfill_runmeta.build()` (same evidence rules, same
"never fabricate" contract — so this is useful before the backfill has been applied).

Guarantees:
  * the EXISTING 13-column schema is preserved exactly, header included;
  * existing rows are never deleted and their values are never rewritten — the only
    edit is appending a marker to `notes` for rows whose `output_dir` is gone;
  * idempotent: a second run reports 0 additions and 0 flags;
  * `key_metric` / `value` / `stage` are left EMPTY for new rows. They cannot be
    derived without interpreting a result, and a guessed headline number in the
    registry is worse than a blank one.

Dry run by default; `--apply` rewrites the CSV in place (after a .bak copy).

Usage:
    python scripts/update_registry.py                    # dry run, prints the delta
    python scripts/update_registry.py --apply
    python scripts/update_registry.py --show-new 20      # preview the rows to be added
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
REPO = os.path.dirname(PROJ)
sys.path.insert(0, HERE)

import backfill_runmeta as BF          # noqa: E402  (reuse: same reconstruction rules)

COLUMNS = ["run_id", "date", "stage", "experiment", "model", "git_commit", "config",
           "seed", "status", "key_metric", "value", "output_dir", "notes"]

MISSING_MARK = "[output_dir MISSING on disk]"
AUTO_NOTE = "auto-added by scripts/update_registry.py"

STATUS_MAP = {"reconstructed": "COMPLETE", "ok": "COMPLETE",
              "incomplete": "INCOMPLETE", "empty": "EMPTY", "unknown": "UNKNOWN"}


def norm_dir(p: str) -> str:
    """Registry `output_dir` cells to a comparable key (they are repo-relative)."""
    if not p:
        return ""
    p = p.strip().rstrip("/")
    if os.path.isabs(p):
        p = os.path.relpath(p, REPO)
    return os.path.normpath(p)


def meta_get(meta, key):
    """Read a field from either RUNMETA flavour: live (flat) or reconstructed (nested)."""
    if not isinstance(meta, dict):
        return None
    if isinstance(meta.get("fields"), dict) and key in meta["fields"]:
        v = meta["fields"][key]
        return v.get("value") if isinstance(v, dict) else v
    v = meta.get(key)
    return v.get("value") if isinstance(v, dict) else v


def load_registry(path):
    with open(path, newline="") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        raise SystemExit(f"{path}: empty")
    header = rows[0]
    if header != COLUMNS:
        raise SystemExit(f"{path}: unexpected schema\n  found:    {header}\n"
                         f"  expected: {COLUMNS}")
    return header, [dict(zip(header, r + [""] * (len(header) - len(r)))) for r in rows[1:]]


def run_record(dpath, dname, log_texts, log_parsed, slurm_idx, shortnames, strict):
    """(status, meta) for one run dir — from RUNMETA.json if present, else rebuilt."""
    rp = os.path.join(dpath, BF.RUNMETA_NAME)
    if os.path.exists(rp):
        try:
            with open(rp) as fh:
                meta = json.load(fh)
            status = meta.get("status")
            if not status:
                dp = os.path.join(dpath, BF.DONE_NAME)
                if os.path.exists(dp):
                    with open(dp) as fh:
                        status = json.load(fh).get("status")
            return (status or "unknown"), meta, bool(meta.get("reconstructed"))
        except Exception:
            pass
    payload = [f for f in sorted(os.listdir(dpath))
               if f not in (BF.RUNMETA_NAME, BF.DONE_NAME)]
    status, meta, _done, _g = BF.build(dpath, dname, payload, strict, log_texts,
                                       log_parsed, slurm_idx, None, shortnames)
    return status, meta, True


def build_row(dname, status, meta, reconstructed, dup_jobs):
    commit = meta_get(meta, "git_commit") or ""
    model = meta_get(meta, "model") or meta_get(meta, "model_from_dirname") or ""
    start = meta_get(meta, "start_ts") or ""
    cohort = meta_get(meta, "cohort")
    seed = meta_get(meta, "seed")
    script = meta_get(meta, "script") or ""
    job = meta_get(meta, "slurm_job_id")

    notes = [AUTO_NOTE + (" from reconstructed RUNMETA" if reconstructed
                          else " from RUNMETA.json")]
    if not commit:
        notes.append("no git commit recoverable")
    if job and dup_jobs.get(job, 0) > 1:
        notes.append(f"job {job} produced {dup_jobs[job]} dirs - DISAMBIGUATE (plan 2.3)")

    return {
        "run_id": dname,
        "date": start[:10],
        "stage": "",
        "experiment": os.path.basename(script)[:-3] if script.endswith(".py")
                      else (meta_get(meta, "phase") or ""),
        "model": model,
        "git_commit": commit[:7],
        "config": f"cohort={cohort}" if cohort else "",
        "seed": "" if seed is None else str(seed),
        "status": STATUS_MAP.get(status, "UNKNOWN"),
        "key_metric": "",
        "value": "",
        "output_dir": norm_dir(os.path.join("doublespeak_causality", "outputs", dname)),
        "notes": "; ".join(notes),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--registry", default=os.path.join(PROJ, "EXPERIMENT_REGISTRY.csv"))
    ap.add_argument("--outputs", default=os.path.join(PROJ, "outputs"))
    ap.add_argument("--logs", default=os.path.join(PROJ, "logs"))
    ap.add_argument("--slurm", default=os.path.join(PROJ, "slurm"))
    ap.add_argument("--apply", action="store_true", help="rewrite the CSV (default: dry run)")
    ap.add_argument("--strict-names", action="store_true",
                    help="passed through to the reconstruction: only summary.json/raw.jsonl count")
    ap.add_argument("--skip-empty", action="store_true",
                    help="do not add rows for dirs that are empty on disk")
    ap.add_argument("--no-flag-missing", action="store_true",
                    help="do not annotate rows whose output_dir no longer exists")
    ap.add_argument("--show-new", type=int, default=0, help="print the first N new rows")
    args = ap.parse_args()

    header, rows = load_registry(args.registry)
    by_dir = {}
    for i, r in enumerate(rows):
        by_dir.setdefault(norm_dir(r["output_dir"]), []).append(i)
    known_ids = {r["run_id"] for r in rows}

    slurm_idx = BF.index_slurm(args.slurm)
    log_texts, log_parsed = BF.index_logs(args.logs)
    shortnames = BF.model_shortnames(log_parsed)

    dirs = sorted(d for d in os.listdir(args.outputs)
                  if os.path.isdir(os.path.join(args.outputs, d)))

    dup_jobs = {}
    for d in dirs:
        info = BF.parse_dirname(d)
        if "slurm_job_id" in info:
            dup_jobs[info["slurm_job_id"]] = dup_jobs.get(info["slurm_job_id"], 0) + 1

    new_rows, matched, skipped = [], 0, 0
    for d in dirs:
        key = norm_dir(os.path.join("doublespeak_causality", "outputs", d))
        if key in by_dir:
            matched += 1
            continue
        p = os.path.join(args.outputs, d)
        status, meta, rec = run_record(p, d, log_texts, log_parsed, slurm_idx,
                                       shortnames, args.strict_names)
        if args.skip_empty and status == "empty":
            skipped += 1
            continue
        new_rows.append(build_row(d, status, meta, rec, dup_jobs))

    # Existing rows whose output_dir is gone (moved, pruned, or never a dir).
    flagged = []
    for r in rows:
        od = r["output_dir"].strip()
        if not od or MISSING_MARK in r["notes"]:
            continue
        if not os.path.exists(os.path.join(REPO, norm_dir(od))):
            flagged.append(r)

    collide = sorted({r["run_id"] for r in new_rows} & known_ids)

    mode = "APPLY" if args.apply else "DRY-RUN (no file written; pass --apply)"
    print(f"update_registry.py [{mode}]  registry={os.path.relpath(args.registry, REPO)}")
    print(f"  existing rows                     : {len(rows)}")
    print(f"  run dirs on disk                  : {len(dirs)}")
    print(f"  dirs already in the registry      : {matched}")
    print(f"  rows to ADD                       : {len(new_rows)}")
    if args.skip_empty:
        print(f"  empty dirs skipped (--skip-empty) : {skipped}")
    from collections import Counter
    for k, v in sorted(Counter(r["status"] for r in new_rows).items()):
        print(f"      status {k:<11} {v}")
    print(f"  new rows carrying a git commit    : "
          f"{sum(1 for r in new_rows if r['git_commit'])}")
    print(f"  existing rows flagged missing     : {len(flagged)}"
          + (" (disabled)" if args.no_flag_missing else ""))
    for r in flagged[:10]:
        print(f"      {r['run_id']}  ->  {r['output_dir']}")
    if collide:
        print(f"  NOTE run_id already used by a row with a different output_dir: {collide}")
    print(f"  registry rows after apply         : {len(rows) + len(new_rows)}"
          f"   (delta +{len(new_rows)})")
    if args.show_new:
        for r in new_rows[:args.show_new]:
            print("      " + " | ".join(r[c] for c in COLUMNS))

    if not args.apply:
        return 0
    if not new_rows and not (flagged and not args.no_flag_missing):
        print("  nothing to do (idempotent no-op)")
        return 0

    if not args.no_flag_missing:
        for r in flagged:
            r["notes"] = (r["notes"] + "; " if r["notes"] else "") + MISSING_MARK
    out = rows + sorted(new_rows, key=lambda r: (r["date"], r["run_id"]))
    shutil.copy2(args.registry, args.registry + ".bak")
    tmp = args.registry + ".tmp"
    with open(tmp, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(out)
    os.replace(tmp, args.registry)
    print(f"  wrote {len(out)} rows (backup at {os.path.basename(args.registry)}.bak)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
