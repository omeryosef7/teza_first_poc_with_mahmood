#!/usr/bin/env python3
"""One-command artifact audit (CAUSAL_CONTINUATION_MASTER_PLAN §2.2 item 10).

Audits `outputs/` against the §2.1 run-directory contract and the committed
provenance records, and exits non-zero on a regression. Runs on the login node
(CPU, stdlib only, no numpy/torch). Fast by default: nothing is hashed unless
`--verify-hashes` is passed, and even then only the files that
`ARTEFACT_MANIFEST.json` lists.

Checks
  A. run-dir inventory ........ total run dirs; how many carry summary.json /
                                RUNMETA.json / DONE.json / raw.jsonl
  B. broken run dirs .......... EMPTY dirs; dirs with raw.jsonl but no summary.json
  C. fixed-name dirs .......... no `_YYYYMMDD_HHMMSS` stamp => clobber-on-rerun
                                (also reports stamped-but-jobless dirs)
  D. job-id collisions ........ one SLURM job id mapping to >1 run dir
  E. orphan runs .............. run dirs with no matching file in logs/
  F. registry drift ........... EXPERIMENT_REGISTRY.csv rows vs disk, both ways
  G. manifest drift ........... ARTEFACT_MANIFEST.json missing / resized /
                                (with --verify-hashes) sha256-drifted files
  H. capacity ................. size of outputs/ and free space on its mount

Severity & exit status
  FAIL  contract violations (empty dirs, raw-without-summary, dead registry
        rows, manifest drift, free space below the hard floor)
  WARN  provenance hazards (fixed names, ambiguous job ids, orphan runs,
        unregistered runs, missing RUNMETA/DONE, low free space)
  exit 0 = no FAIL findings (and, with --baseline, nothing got worse)
  exit 1 = at least one FAIL finding, or any counter worse than the baseline
  exit 2 = usage / IO error

Because the repo is *currently* in violation of §2.1, a bare run exits 1 by
design. To use this as a ratchet, freeze today's numbers and compare:

  python scripts/audit_artifacts.py --write-baseline reports/audit_baseline.json
  python scripts/audit_artifacts.py --baseline reports/audit_baseline.json

Usage:
  python scripts/audit_artifacts.py                     # readable table
  python scripts/audit_artifacts.py -v                  # + full offender lists
  python scripts/audit_artifacts.py --json              # machine output
  python scripts/audit_artifacts.py --verify-hashes     # recompute manifest sha256
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
from collections import defaultdict

# --- run-dir naming ---------------------------------------------------------
# Contract: outputs/{phase}_{cohort}_{YYYYMMDD}_{HHMMSS}_{jobid}/
RE_TS = re.compile(r"_(\d{8})_(\d{6})(?=_|$)")
RE_JOBID_TAIL = re.compile(r"_(\d{5,})$")
RE_JOBID_ANY = re.compile(r"(\d{5,})")

CONTRACT_FILES = ("summary.json", "RUNMETA.json", "DONE.json", "raw.jsonl")

# counters that must never grow; compared against --baseline
RATCHET_KEYS = [
    "empty_dirs",
    "raw_without_summary",
    "fixed_name_dirs",
    "ambiguous_job_ids",
    "dirs_in_ambiguous_jobs",
    "dirs_without_log",
    "registry_rows_dead_path",
    "unregistered_run_dirs",
    "manifest_missing",
    "manifest_size_drift",
    "manifest_hash_drift",
    "manifest_drift_total",
]


class Report:
    """Collects findings; mirrors the ok/WARN/FATAL idiom of validate_data_integrity.py."""

    def __init__(self):
        self.rows = []  # (severity, check, message, detail_list)

    def add(self, sev, check, msg, detail=None):
        self.rows.append((sev, check, msg, list(detail or [])))

    def ok(self, check, msg, detail=None):
        self.add("ok", check, msg, detail)

    def warn(self, check, msg, detail=None):
        self.add("WARN", check, msg, detail)

    def fail(self, check, msg, detail=None):
        self.add("FAIL", check, msg, detail)

    def n(self, sev):
        return sum(1 for r in self.rows if r[0] == sev)


def norm_token(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def human(nbytes: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(nbytes) < 1024.0 or unit == "TB":
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024.0
    return f"{nbytes:.1f} TB"


def sha256_file(path: str, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def tree_bytes(root: str):
    """Total bytes + file count under root (metadata only; ~0.3 s for 9 GB)."""
    total, nfiles = 0, 0
    for dirpath, _dirnames, filenames in os.walk(root):
        for f in filenames:
            try:
                total += os.lstat(os.path.join(dirpath, f)).st_size
                nfiles += 1
            except OSError:
                pass
    return total, nfiles


# ---------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------
def scan_run_dirs(outputs_dir: str):
    """Top-level subdirectories of outputs/ are the run dirs."""
    runs = {}
    for name in sorted(os.listdir(outputs_dir)):
        p = os.path.join(outputs_dir, name)
        if not os.path.isdir(p):
            continue
        try:
            entries = os.listdir(p)
        except OSError:
            entries = []
        runs[name] = {
            "path": p,
            "n_entries": len(entries),
            "files": set(entries),
        }
    return runs


def check_inventory(rep, runs):
    n = len(runs)
    rep.ok("A.inventory", f"{n} run dirs under outputs/")
    counts = {f: sum(1 for r in runs.values() if f in r["files"]) for f in CONTRACT_FILES}
    for f in CONTRACT_FILES:
        c = counts[f]
        pct = 100.0 * c / n if n else 0.0
        msg = f"{f:<14} present in {c:>4}/{n} run dirs ({pct:5.1f}%)"
        if f == "summary.json":
            rep.ok("A.inventory", msg)
        else:
            # RUNMETA/DONE are the §2.1 contract files that do not exist yet
            (rep.ok if c == n else rep.warn)("A.inventory", msg)
    return counts


def check_broken(rep, runs):
    empty = sorted(k for k, v in runs.items() if v["n_entries"] == 0)
    raw_no_sum = sorted(
        k for k, v in runs.items()
        if "raw.jsonl" in v["files"] and "summary.json" not in v["files"]
    )
    (rep.ok if not empty else rep.fail)(
        "B.broken", f"{len(empty)} EMPTY run dirs (no files at all)", empty)
    (rep.ok if not raw_no_sum else rep.fail)(
        "B.broken", f"{len(raw_no_sum)} dirs with raw.jsonl but no summary.json (aborted runs)",
        raw_no_sum)
    return empty, raw_no_sum


def check_names(rep, runs):
    fixed, ts_no_job = [], []
    for name in runs:
        has_ts = RE_TS.search(name) is not None
        has_job = RE_JOBID_TAIL.search(name) is not None
        if not has_ts:
            fixed.append(name)
        elif not has_job:
            ts_no_job.append(name)
    fixed.sort()
    ts_no_job.sort()
    (rep.ok if not fixed else rep.warn)(
        "C.names",
        f"{len(fixed)} fixed-name dirs (no _YYYYMMDD_HHMMSS stamp) -- clobber-on-rerun",
        fixed)
    (rep.ok if not ts_no_job else rep.warn)(
        "C.names",
        f"{len(ts_no_job)} timestamped dirs with no trailing _<jobid>",
        ts_no_job)
    return fixed, ts_no_job


def check_job_collisions(rep, runs):
    by_job = defaultdict(list)
    for name in runs:
        m = RE_JOBID_TAIL.search(name)
        if m:
            by_job[m.group(1)].append(name)
    multi = {j: sorted(v) for j, v in by_job.items() if len(v) > 1}
    n_dirs = sum(len(v) for v in multi.values())
    detail = [f"{j}: " + ", ".join(v) for j, v in sorted(multi.items())]
    (rep.ok if not multi else rep.warn)(
        "D.jobids",
        f"{len(multi)} SLURM job ids map to >1 run dir ({n_dirs} dirs, ambiguous provenance)",
        detail)
    return multi, n_dirs


def check_logs(rep, runs, logs_dir):
    if not os.path.isdir(logs_dir):
        rep.fail("E.logs", f"logs dir not found: {logs_dir}")
        return [], [], 0
    log_names = os.listdir(logs_dir)
    log_jobs = set()
    for l in log_names:
        log_jobs.update(RE_JOBID_ANY.findall(l))
    stems = [norm_token(os.path.splitext(l)[0]) for l in log_names]
    stems = [s for s in stems if s]

    no_log_jobid, no_log_named = [], []
    for name in sorted(runs):
        m = RE_JOBID_TAIL.search(name)
        if m:
            if m.group(1) not in log_jobs:
                no_log_jobid.append(name)
        else:
            nd = norm_token(name)
            if not any(s in nd or nd in s for s in stems):
                no_log_named.append(name)
    total = len(no_log_jobid) + len(no_log_named)
    rep.ok("E.logs", f"{len(log_names)} files in logs/, {len(log_jobs)} distinct job ids")
    (rep.ok if not no_log_jobid else rep.warn)(
        "E.logs",
        f"{len(no_log_jobid)} run dirs whose job id has NO logs/ file",
        no_log_jobid)
    (rep.ok if not no_log_named else rep.warn)(
        "E.logs",
        f"{len(no_log_named)} job-id-less run dirs with no name-matching logs/ file",
        no_log_named)
    return no_log_jobid, no_log_named, total


def _resolve_registry_path(val, project_dir, repo_root):
    """Registry output_dir values are repo-root-relative ('doublespeak_causality/outputs/x')
    or project-relative ('outputs/x'). Return (abs_path_or_None, existed)."""
    val = (val or "").strip().rstrip("/")
    if not val:
        return None, False
    cands = []
    if os.path.isabs(val):
        cands.append(val)
    else:
        cands += [os.path.join(repo_root, val), os.path.join(project_dir, val)]
    for c in cands:
        if os.path.exists(c):
            return c, True
    return cands[0], False


def check_registry(rep, runs, registry_path, outputs_dir, project_dir, repo_root):
    if not os.path.exists(registry_path):
        rep.fail("F.registry", f"EXPERIMENT_REGISTRY.csv not found: {registry_path}")
        return {"rows": 0, "dead": [], "unregistered": sorted(runs), "non_run_dir": []}
    with open(registry_path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    dead, non_run_dir, registered = [], [], set()
    for r in rows:
        rid = (r.get("run_id") or "?").strip()
        raw = (r.get("output_dir") or "").strip()
        if not raw:
            non_run_dir.append(f"{rid}: <empty output_dir>")
            continue
        path, existed = _resolve_registry_path(raw, project_dir, repo_root)
        if not existed:
            dead.append(f"{rid}: {raw}")
            continue
        # is it one of our run dirs?
        if os.path.isdir(path) and os.path.dirname(os.path.abspath(path)) == os.path.abspath(outputs_dir):
            base = os.path.basename(os.path.abspath(path))
            if base in runs:
                registered.add(base)
                continue
        non_run_dir.append(f"{rid}: {raw}")
    unregistered = sorted(set(runs) - registered)

    rep.ok("F.registry", f"{len(rows)} registry rows; {len(registered)} resolve to a run dir")
    (rep.ok if not dead else rep.fail)(
        "F.registry", f"{len(dead)} registry rows whose output_dir does NOT exist", dead)
    (rep.ok if not non_run_dir else rep.warn)(
        "F.registry",
        f"{len(non_run_dir)} registry rows pointing at a file / non-run-dir path",
        non_run_dir)
    (rep.ok if not unregistered else rep.warn)(
        "F.registry", f"{len(unregistered)} run dirs with NO registry row", unregistered)
    return {"rows": len(rows), "dead": dead, "unregistered": unregistered,
            "non_run_dir": non_run_dir, "registered": sorted(registered)}


def check_manifest(rep, manifest_path, project_dir, repo_root, verify_hashes):
    if not os.path.exists(manifest_path):
        rep.fail("G.manifest", f"ARTEFACT_MANIFEST.json not found: {manifest_path}")
        return {"n_files": 0, "missing": [], "size_drift": [], "hash_drift": [],
                "hashed_bytes": 0, "verified": False}
    with open(manifest_path) as fh:
        man = json.load(fh)
    files = man.get("files", [])
    missing, size_drift, hash_drift = [], [], []
    hashed_bytes = 0
    for ent in files:
        rel = ent.get("path", "")
        path, existed = _resolve_registry_path(rel, project_dir, repo_root)
        if not existed:
            missing.append(rel)
            continue
        try:
            sz = os.path.getsize(path)
        except OSError as e:
            missing.append(f"{rel} ({e})")
            continue
        if ent.get("bytes") is not None and sz != ent["bytes"]:
            size_drift.append(f"{rel} (manifest {ent['bytes']} B, disk {sz} B)")
            continue  # size already proves drift; do not pay for the hash
        if verify_hashes and ent.get("sha256"):
            hashed_bytes += sz
            if sha256_file(path) != ent["sha256"]:
                hash_drift.append(rel)

    rep.ok("G.manifest",
           f"{len(files)} files listed in ARTEFACT_MANIFEST.json "
           f"({human(sum(e.get('bytes', 0) or 0 for e in files))})")
    (rep.ok if not missing else rep.fail)(
        "G.manifest", f"{len(missing)} manifest files MISSING from disk", missing)
    (rep.ok if not size_drift else rep.fail)(
        "G.manifest", f"{len(size_drift)} manifest files with a SIZE mismatch", size_drift)
    if verify_hashes:
        (rep.ok if not hash_drift else rep.fail)(
            "G.manifest",
            f"{len(hash_drift)} manifest files with sha256 DRIFT "
            f"({human(hashed_bytes)} hashed)",
            hash_drift)
    else:
        rep.warn("G.manifest",
                 "sha256 not recomputed (pass --verify-hashes); size check only")
    return {"n_files": len(files), "missing": missing, "size_drift": size_drift,
            "hash_drift": hash_drift, "hashed_bytes": hashed_bytes,
            "verified": bool(verify_hashes)}


def check_capacity(rep, outputs_dir, warn_gb, fail_gb):
    total, nfiles = tree_bytes(outputs_dir)
    st = os.statvfs(outputs_dir)
    free = st.f_bavail * st.f_frsize
    cap = st.f_blocks * st.f_frsize
    used_pct = 100.0 * (1.0 - (st.f_bfree * st.f_frsize) / cap) if cap else 0.0
    rep.ok("H.capacity", f"outputs/ = {human(total)} in {nfiles} files")
    msg = (f"mount holding outputs/: {human(free)} free of {human(cap)} "
           f"({used_pct:.0f}% used)")
    free_gb = free / 2 ** 30
    if free_gb < fail_gb:
        rep.fail("H.capacity", msg + f" -- below hard floor {fail_gb:g} GB")
    elif free_gb < warn_gb:
        rep.warn("H.capacity", msg + f" -- below warn threshold {warn_gb:g} GB")
    else:
        rep.ok("H.capacity", msg)
    return {"outputs_bytes": total, "outputs_files": nfiles,
            "free_bytes": free, "capacity_bytes": cap, "used_pct": used_pct}


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------
SEV_ORDER = {"FAIL": 0, "WARN": 1, "ok": 2}


def render_table(rep, counters, meta, max_detail):
    w = 78
    print("=" * w)
    print("ARTIFACT AUDIT  --  CAUSAL_CONTINUATION_MASTER_PLAN §2.2 item 10")
    print(f"project : {meta['project_dir']}")
    print(f"when    : {meta['timestamp']}   ({meta['elapsed_s']:.2f} s)")
    print("=" * w)
    cur = None
    for sev, check, msg, detail in rep.rows:
        sec = check.split(".", 1)[0]
        if sec != cur:
            cur = sec
            print()
            print(f"[{check.split('.', 1)[1].upper()}]")
        tag = {"ok": "  ok  ", "WARN": " WARN ", "FAIL": " FAIL "}[sev]
        print(f"{tag}| {msg}")
        if detail and sev != "ok":
            shown = detail if max_detail < 0 else detail[:max_detail]
            for d in shown:
                print(f"      |     - {d}")
            if len(detail) > len(shown):
                print(f"      |     ... {len(detail) - len(shown)} more "
                      f"(use -v for the full list)")
    print()
    print("-" * w)
    print("COUNTERS")
    for k in RATCHET_KEYS:
        print(f"  {k:<26} {counters[k]}")
    print("-" * w)
    print(f"SUMMARY  {rep.n('ok')} ok / {rep.n('WARN')} WARN / {rep.n('FAIL')} FAIL")


# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="One-command artifact/provenance audit for doublespeak_causality.")
    here = os.path.dirname(os.path.abspath(__file__))
    default_project = os.path.dirname(here)
    ap.add_argument("--project-dir", default=default_project,
                    help="project root (default: parent of this script's dir)")
    ap.add_argument("--outputs", default=None, help="override outputs/ path")
    ap.add_argument("--logs", default=None, help="override logs/ path")
    ap.add_argument("--registry", default=None, help="override EXPERIMENT_REGISTRY.csv path")
    ap.add_argument("--manifest", default=None, help="override ARTEFACT_MANIFEST.json path")
    ap.add_argument("--verify-hashes", action="store_true",
                    help="recompute sha256 for manifest-listed files (slow; opt-in)")
    ap.add_argument("--free-warn-gb", type=float, default=500.0,
                    help="WARN when free space on the outputs mount is below this (default 500)")
    ap.add_argument("--free-fail-gb", type=float, default=50.0,
                    help="FAIL when free space is below this (default 50)")
    ap.add_argument("--baseline", default=None,
                    help="JSON file of frozen counters; exit 1 only if a counter got worse")
    ap.add_argument("--write-baseline", default=None,
                    help="write the current counters to this path and exit 0")
    ap.add_argument("--max-detail", type=int, default=8,
                    help="offenders printed per finding in table mode (default 8)")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="print every offender (max-detail = unlimited)")
    ap.add_argument("--json", dest="as_json", action="store_true",
                    help="machine-readable output instead of the table")
    args = ap.parse_args(argv)

    t0 = time.time()
    project_dir = os.path.abspath(args.project_dir)
    repo_root = os.path.dirname(project_dir)
    outputs_dir = os.path.abspath(args.outputs or os.path.join(project_dir, "outputs"))
    logs_dir = os.path.abspath(args.logs or os.path.join(project_dir, "logs"))
    registry = os.path.abspath(args.registry or os.path.join(project_dir, "EXPERIMENT_REGISTRY.csv"))
    manifest = os.path.abspath(args.manifest or os.path.join(project_dir, "ARTEFACT_MANIFEST.json"))

    if not os.path.isdir(outputs_dir):
        print(f"ERROR: outputs dir not found: {outputs_dir}", file=sys.stderr)
        return 2

    rep = Report()
    runs = scan_run_dirs(outputs_dir)
    file_counts = check_inventory(rep, runs)
    empty, raw_no_sum = check_broken(rep, runs)
    fixed, ts_no_job = check_names(rep, runs)
    multi_jobs, dirs_in_multi = check_job_collisions(rep, runs)
    no_log_jobid, no_log_named, no_log_total = check_logs(rep, runs, logs_dir)
    reg = check_registry(rep, runs, registry, outputs_dir, project_dir, repo_root)
    man = check_manifest(rep, manifest, project_dir, repo_root, args.verify_hashes)
    cap = check_capacity(rep, outputs_dir, args.free_warn_gb, args.free_fail_gb)

    counters = {
        "run_dirs": len(runs),
        "with_summary_json": file_counts.get("summary.json", 0),
        "with_runmeta_json": file_counts.get("RUNMETA.json", 0),
        "with_done_json": file_counts.get("DONE.json", 0),
        "with_raw_jsonl": file_counts.get("raw.jsonl", 0),
        "empty_dirs": len(empty),
        "raw_without_summary": len(raw_no_sum),
        "fixed_name_dirs": len(fixed),
        "stamped_without_jobid": len(ts_no_job),
        "ambiguous_job_ids": len(multi_jobs),
        "dirs_in_ambiguous_jobs": dirs_in_multi,
        "dirs_without_log": no_log_total,
        "dirs_without_log_by_jobid": len(no_log_jobid),
        "dirs_without_log_by_name": len(no_log_named),
        "registry_rows": reg["rows"],
        "registry_rows_dead_path": len(reg["dead"]),
        "registry_rows_non_run_dir": len(reg["non_run_dir"]),
        "unregistered_run_dirs": len(reg["unregistered"]),
        "manifest_files": man["n_files"],
        "manifest_missing": len(man["missing"]),
        "manifest_size_drift": len(man["size_drift"]),
        "manifest_hash_drift": len(man["hash_drift"]) if man["verified"] else 0,
        # a size mismatch short-circuits the hash check, so track the union too
        "manifest_drift_total": (len(man["missing"]) + len(man["size_drift"])
                                 + (len(man["hash_drift"]) if man["verified"] else 0)),
        "manifest_hashes_verified": int(man["verified"]),
        "outputs_bytes": cap["outputs_bytes"],
        "outputs_files": cap["outputs_files"],
        "free_bytes": cap["free_bytes"],
    }

    # --- regression logic ---------------------------------------------------
    regressions = []
    baseline = None
    if args.baseline:
        try:
            with open(args.baseline) as fh:
                baseline = json.load(fh).get("counters", {})
        except (OSError, ValueError) as e:
            print(f"ERROR: cannot read baseline {args.baseline}: {e}", file=sys.stderr)
            return 2
        for k in RATCHET_KEYS:
            if k in baseline and counters[k] > baseline[k]:
                regressions.append(f"{k}: {baseline[k]} -> {counters[k]}")
                rep.fail("Z.baseline", f"REGRESSION {k}: {baseline[k]} -> {counters[k]}")
        if not regressions:
            rep.ok("Z.baseline", f"no counter worse than baseline {args.baseline}")

    meta = {
        "project_dir": project_dir,
        "outputs_dir": outputs_dir,
        "logs_dir": logs_dir,
        "registry": registry,
        "manifest": manifest,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "elapsed_s": time.time() - t0,
        "verify_hashes": bool(args.verify_hashes),
        "baseline": args.baseline,
    }

    payload = {
        "meta": meta,
        "counters": counters,
        "findings": [
            {"severity": s, "check": c, "message": m, "detail": d}
            for s, c, m, d in rep.rows
        ],
        "regressions": regressions,
        "n_ok": rep.n("ok"), "n_warn": rep.n("WARN"), "n_fail": rep.n("FAIL"),
    }

    if args.write_baseline:
        with open(args.write_baseline, "w") as fh:
            json.dump({"meta": meta, "counters": counters}, fh, indent=2, sort_keys=True)
        print(f"baseline written: {args.write_baseline}")
        return 0

    if args.as_json:
        payload["exit_code"] = 1 if (rep.n("FAIL") > 0 if baseline is None else bool(regressions)) else 0
        json.dump(payload, sys.stdout, indent=2, sort_keys=False)
        sys.stdout.write("\n")
        return payload["exit_code"]

    render_table(rep, counters, meta, -1 if args.verbose else args.max_detail)
    if baseline is None:
        code = 1 if rep.n("FAIL") > 0 else 0
        print(f"EXIT     {code}  ({'FAIL findings present' if code else 'clean'}; "
              f"use --baseline to ratchet instead)")
    else:
        code = 1 if regressions else 0
        print(f"EXIT     {code}  ({'REGRESSION vs baseline' if code else 'no regression vs baseline'})")
    return code


if __name__ == "__main__":
    sys.exit(main())
