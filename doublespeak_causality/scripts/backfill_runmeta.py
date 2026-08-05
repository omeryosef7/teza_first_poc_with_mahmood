#!/usr/bin/env python
"""backfill_runmeta.py — reconstruct RUNMETA.json / DONE.json for pre-contract runs.

Plan §2.2 item 4. Every run dir under `outputs/` that predates
`ds_common.write_runmeta()` has no provenance record at all. This script reconstructs
ONLY what is actually sourceable, and marks every reconstructed field with
`"source": "reconstructed"` plus the concrete evidence it came from:

  dir_name      the run-dir basename: timestamp, trailing SLURM job id, phase, and
                (when embedded) the model short-name.
  log:<file>    logs/<prefix>_<jobid>.out, located by the job id in the dir name, or by
                the dir name appearing verbatim inside the log body. Yields the git
                commit (`git=<sha>`), GPU (`GPU ok: ...`), node, model id, torch version.
  slurm:<file>  the sbatch wrapper whose `--output=...logs/<prefix>_%j.out` matches the
                log filename -> the python script that was invoked, and the wrapper's
                argv TEMPLATE (unexpanded `$VARS` — recorded as a template, never as
                the real argv).
  summary.json  the run's own aggregates: model, cohort, n_rows, seed when present.
  mtime         filesystem timestamps, used only for end_ts / wall_seconds.

NEVER fabricates. A field that cannot be sourced is omitted from `fields` and listed in
`unknown_fields` with a reason. Nothing already on disk is overwritten.

Status assigned in DONE.json:
  reconstructed  raw + summary present (the run completed)
  incomplete     raw present, summary missing (aborted run)
  empty          the dir is empty
  unknown        neither raw nor summary (non-standard payload; files are listed)

Run dirs that predate the naming contract use legacy artifact names
(`necessity_raw.jsonl` / `necessity_summary.json`); those count as raw/summary and the
exact filenames used are recorded. `--strict-names` restricts to `raw.jsonl` /
`summary.json` only.

Login-node only, stdlib only, read-only unless --apply.

Usage:
    python scripts/backfill_runmeta.py                 # dry run (default)
    python scripts/backfill_runmeta.py --apply
    python scripts/backfill_runmeta.py --apply --report-json outputs/backfill_report.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)                      # doublespeak_causality/
REPO = os.path.dirname(PROJ)

RUNMETA_NAME = "RUNMETA.json"
DONE_NAME = "DONE.json"

# ---- dir-name grammar ------------------------------------------------------ #
# <phase>[_<Model-Short-Name>]_<YYYYMMDD>_<HHMMSS>[_<tag>]_[<jobid>]
RE_JOBID = re.compile(r"_(\d{5,8})$")
RE_TS = re.compile(r"_(\d{8})_(\d{6})(?=_|$)")

# ---- log-line grammar ------------------------------------------------------ #
RE_GIT = re.compile(r"^git=([0-9a-f]{7,40})\s*$", re.M)
RE_GPU = re.compile(r"^GPU ok:\s*(.+?)\s*$", re.M)
RE_NODE = re.compile(r"^(n-\d+|[a-z]{1,10}-\d{1,4})\s*$", re.M)
RE_TORCH = re.compile(r"torch[= ]([0-9]+\.[0-9]+\.[0-9]+[^\s,;]*)")
RE_MODEL = re.compile(
    r"\b((?:meta-llama|Qwen|microsoft|deepseek-ai|google|mistralai|HuggingFaceH4)"
    r"/[A-Za-z0-9_.\-]+)")
# ---- sbatch grammar -------------------------------------------------------- #
RE_SB_OUT = re.compile(r"--output=\S*logs/([A-Za-z0-9_\-]+)_%j\.out")
RE_SB_PY = re.compile(r"^\s*(?:srun\s+)?\S*python\b[^\n]*?\s(\S+\.py)\b")
RE_LOGNAME = re.compile(r"^(.*)_(\d{5,8})\.(?:out|err)$")


def _rel(path: str) -> str:
    """Repo-relative path, or the absolute path when it lies outside the repo."""
    rp = os.path.relpath(os.path.abspath(path), REPO)
    return os.path.abspath(path) if rp.startswith("..") else rp


def _field(value, source: str, evidence: str):
    """Every reconstructed value carries where it came from (plan §2.2 item 4)."""
    return {"value": value, "source": "reconstructed", "evidence": evidence,
            "source_kind": source}


# --------------------------------------------------------------------------- #
# Index building
# --------------------------------------------------------------------------- #
def index_slurm(slurm_dir: str):
    """log-filename prefix -> {'script': <wrapper .sh>, 'py': [...], 'argv_template': str}"""
    idx = {}
    if not os.path.isdir(slurm_dir):
        return idx
    for fn in sorted(os.listdir(slurm_dir)):
        p = os.path.join(slurm_dir, fn)
        if not os.path.isfile(p):
            continue
        try:
            txt = open(p, errors="replace").read()
        except Exception:
            continue
        m = RE_SB_OUT.search(txt)
        if not m:
            continue
        pys, argvs = [], []
        lines = txt.splitlines()
        for i, ln in enumerate(lines):
            mm = RE_SB_PY.match(ln)
            if not mm:
                continue
            pys.append(mm.group(1))
            cmd, j = [ln.strip()], i          # follow `\` line continuations
            while cmd[-1].endswith("\\") and j + 1 < len(lines):
                j += 1
                cmd.append(lines[j].strip())
            argvs.append(" ".join(c.rstrip("\\").strip() for c in cmd))
        prev = idx.get(m.group(1))
        if prev is not None:                 # ambiguous prefix: keep both, trust neither
            prev["wrapper"] = prev["wrapper"] + "+" + fn
            prev["ambiguous"] = True
            continue
        idx[m.group(1)] = {"wrapper": fn, "py": sorted(set(pys)),
                           "argv_template": argvs[0] if len(set(argvs)) == 1 else None,
                           "ambiguous": False}
    return idx


def index_logs(logs_dir: str):
    """Read every log once. Returns (name -> text, name -> parsed fields)."""
    texts, parsed = {}, {}
    if not os.path.isdir(logs_dir):
        return texts, parsed
    for fn in sorted(os.listdir(logs_dir)):
        if not fn.endswith((".out", ".log")):
            continue
        p = os.path.join(logs_dir, fn)
        try:
            txt = open(p, errors="replace").read()
        except Exception:
            continue
        texts[fn] = txt
        head = "\n".join(txt.splitlines()[:80])
        g, gpu = RE_GIT.search(txt), RE_GPU.search(txt)
        node, tv = RE_NODE.search(head), RE_TORCH.search(head)
        mm = RE_MODEL.search(head)
        parsed[fn] = {
            "git_commit": g.group(1) if g else None,
            "gpu": gpu.group(1) if gpu else None,
            "node": node.group(1) if node else None,
            "torch": tv.group(1) if tv else None,
            "model": mm.group(1) if mm else None,
        }
    return texts, parsed


# --------------------------------------------------------------------------- #
# Per-dir reconstruction
# --------------------------------------------------------------------------- #
def classify(files, strict_names: bool):
    """-> (status, summary_file|None, raw_file|None)"""
    if not files:
        return "empty", None, None
    summary = "summary.json" if "summary.json" in files else None
    raw = "raw.jsonl" if "raw.jsonl" in files else None
    if not strict_names:
        if summary is None:
            cand = sorted(f for f in files if f.endswith("_summary.json"))
            summary = cand[0] if cand else None
        if raw is None:
            cand = sorted(f for f in files if f.endswith("_raw.jsonl"))
            raw = cand[0] if cand else None
    if raw and summary:
        return "reconstructed", summary, raw
    if raw and not summary:
        return "incomplete", summary, raw
    return "unknown", summary, raw


def parse_dirname(name: str):
    """Everything the dir name itself proves. No guessing."""
    out = {}
    rest = name
    m = RE_JOBID.search(rest)
    if m:
        out["slurm_job_id"] = m.group(1)
        rest = rest[: m.start()]
    m = RE_TS.search(name)
    if m:
        d, t = m.group(1), m.group(2)
        out["start_ts"] = f"{d[:4]}-{d[4:6]}-{d[6:8]}T{t[:2]}:{t[2:4]}:{t[4:6]}"
        out["date"] = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
        out["phase"] = name[: m.start()]
        tail = rest[m.end():].strip("_")
        if tail:
            out["tag"] = tail
    else:
        out["phase"] = rest
    return out


def count_rows(path: str):
    """Line count of raw.jsonl. Opened in BINARY and never decoded — this repo's raw
    rows may sit next to harmful text and must not be materialised as strings."""
    try:
        n = 0
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                n += chunk.count(b"\n")
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
        if size:
            with open(path, "rb") as fh:
                fh.seek(max(0, size - 1))
                if fh.read(1) != b"\n":
                    n += 1
        return n
    except Exception:
        return None


def read_summary(path: str):
    """Pull ONLY the structural keys named in the §2.1 contract. Never returns text."""
    try:
        with open(path) as fh:
            j = json.load(fh)
    except Exception:
        return {}
    if not isinstance(j, dict):
        return {}
    out = {}
    for k in ("model", "cohort", "n_rows", "seed", "n_valid_examples", "n_valid"):
        v = j.get(k)
        if isinstance(v, (str, int, float, bool)):
            out[k] = v
    return out


def find_logs(dname: str, dinfo, log_texts):
    """(candidate log filenames, how they were matched). Job id first, dir name second."""
    job = dinfo.get("slurm_job_id")
    if job:
        hits = sorted(f for f in log_texts if RE_LOGNAME.match(f)
                      and RE_LOGNAME.match(f).group(2) == job)
        if hits:
            return hits, "jobid_in_log_filename"
    hits = sorted(f for f in log_texts if dname in log_texts[f])
    if hits:
        return hits, "run_dir_path_printed_in_log"
    return [], None


def model_shortnames(log_parsed):
    """{short-name -> full HF id} for every model id that appears in the logs.

    Many run dirs embed the model SHORT name (`..._Llama-3.1-8B-Instruct_2026...`) but
    have no matching log. Resolving that short name against ids actually observed in
    this project's logs is an inference, not a reading, so it is recorded under the
    separate key `model_from_dirname` with the inference spelled out in `evidence` —
    never merged into `model`.
    """
    out = {}
    for p in log_parsed.values():
        mid = p.get("model")
        if mid and "/" in mid:
            out.setdefault(mid.split("/", 1)[1], mid)
    return out


def build(dpath, dname, files, strict_names, log_texts, log_parsed, slurm_idx,
          generator_commit, shortnames=None):
    status, summary_f, raw_f = classify(files, strict_names)
    dinfo = parse_dirname(dname)

    fields = {}
    unknown = {}

    fields["run_id"] = _field(dname, "dir_name", "run-dir basename")
    for key in ("slurm_job_id", "start_ts", "phase", "tag"):
        if key in dinfo:
            fields[key] = _field(dinfo[key], "dir_name", f"parsed from dir name {dname!r}")
    if "slurm_job_id" not in dinfo:
        unknown["slurm_job_id"] = "dir name has no trailing job id"
    if "start_ts" not in dinfo:
        unknown["start_ts"] = "dir name has no YYYYMMDD_HHMMSS stamp"

    for short, full in sorted((shortnames or {}).items(), key=lambda kv: -len(kv[0])):
        if short in dname:
            fields["model_from_dirname"] = _field(
                full, "dir_name",
                f"dir name contains the short name {short!r}; the only HF id with that "
                f"short name in this project's logs is {full!r} (INFERENCE, not a reading)")
            break

    logs, how = find_logs(dname, dinfo, log_texts)
    if logs:
        fields["log_files"] = _field([f"logs/{f}" for f in logs], "log", how)
        for key in ("git_commit", "gpu", "torch", "model"):
            vals = sorted({log_parsed[f][key] for f in logs if log_parsed[f].get(key)})
            if len(vals) == 1:
                fields[key] = _field(vals[0], "log", f"logs/{logs[0]} ({how})")
            elif len(vals) > 1:
                unknown[key] = f"conflicting values across {len(logs)} matched logs"
            else:
                unknown[key] = f"not printed in {len(logs)} matched log(s)"
        nodes = sorted({log_parsed[f]["node"] for f in logs if log_parsed[f].get("node")})
        if len(nodes) == 1:
            fields["slurm_nodelist"] = _field(nodes[0], "log", f"logs/{logs[0]}")
        # log filename prefix -> sbatch wrapper -> python script actually invoked
        wraps = {}
        for f in logs:
            m = RE_LOGNAME.match(f)
            if m and m.group(1) in slurm_idx:
                wraps[m.group(1)] = slurm_idx[m.group(1)]
        if len(wraps) == 1:
            pref, w = next(iter(wraps.items()))
            if not w["ambiguous"]:
                fields["slurm_wrapper"] = _field(
                    f"slurm/{w['wrapper']}", "slurm",
                    f"--output=logs/{pref}_%j.out matches the run's log filename")
                if len(w["py"]) == 1:
                    fields["script"] = _field(w["py"][0], "slurm",
                                              f"python invocation in slurm/{w['wrapper']}")
                elif w["py"]:
                    unknown["script"] = (f"slurm/{w['wrapper']} invokes {len(w['py'])} "
                                         f"scripts: {w['py']}")
                if w["argv_template"]:
                    fields["argv_template"] = _field(
                        w["argv_template"], "slurm",
                        f"UNEXPANDED shell template from slurm/{w['wrapper']}; "
                        f"$VARS were not captured, this is NOT the real argv")
        elif len(wraps) > 1:
            unknown["script"] = f"matched logs map to {len(wraps)} different wrappers"
    else:
        fields["log_files"] = _field([], "log", "no log matched by job id or dir name")
        for key in ("git_commit", "gpu", "torch", "model", "script", "slurm_nodelist"):
            unknown[key] = "no matching log file found"

    if summary_f:
        s = read_summary(os.path.join(dpath, summary_f))
        for k, v in s.items():
            key = {"n_valid_examples": "n_rows", "n_valid": "n_rows"}.get(k, k)
            if key in fields and fields[key]["value"] != v:
                continue                       # log/dir evidence wins; do not overwrite
            fields[key] = _field(v, "summary", f"{summary_f}[{k!r}]")
        if "seed" not in fields:
            unknown["seed"] = "not recorded anywhere: absent from summary.json and logs"
    else:
        unknown["seed"] = "no summary.json and seed is not printed to logs"

    for k in ("argv", "args", "revision", "tokenizer_hash", "dtype",
              "attn_implementation", "chat_template_hash", "git_dirty", "python",
              "transformers"):
        unknown.setdefault(k, "not recoverable: never written to disk or logs")

    meta = {
        "schema": "RUNMETA/1",
        "reconstructed": True,
        "status": status,
        "run_id": dname,
        "output_dir": _rel(dpath),
        "artifacts": {"summary": summary_f, "raw": raw_f,
                      "n_files": len(files), "files": sorted(files)[:50]},
        "fields": fields,
        "unknown_fields": unknown,
        "backfill": {
            "tool": "doublespeak_causality/scripts/backfill_runmeta.py",
            "generated_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "generator_git_commit": generator_commit,
            "warning": ("Reconstructed after the fact. Every value carries its source. "
                        "Absent fields were NOT knowable and were not invented."),
        },
    }

    done = {
        "schema": "DONE/1",
        "reconstructed": True,
        "run_id": dname,
        "status": status,
    }
    if raw_f:
        n = count_rows(os.path.join(dpath, raw_f))
        done["rows_written"] = (_field(n, "raw_file", f"newline count of {raw_f}")
                                if n is not None else None)
    else:
        done["rows_written"] = None
    mt = [os.path.getmtime(os.path.join(dpath, f)) for f in files
          if os.path.exists(os.path.join(dpath, f))]
    if mt:
        end = max(mt)
        done["end_ts"] = _field(time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(end)),
                                "mtime", "latest mtime in the run dir")
        st = fields.get("start_ts")
        if st:
            try:
                t0 = time.mktime(time.strptime(st["value"], "%Y-%m-%dT%H:%M:%S"))
                done["wall_seconds"] = _field(
                    round(end - t0, 1), "mtime",
                    "latest mtime minus the dir-name start timestamp (upper bound: "
                    "post-hoc edits to files in the dir inflate it)")
            except Exception:
                done["wall_seconds"] = None
        else:
            done["wall_seconds"] = None
    else:
        done["end_ts"] = None
        done["wall_seconds"] = None
    done["backfill"] = meta["backfill"]
    return status, meta, done, bool(fields.get("git_commit"))


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--outputs", default=os.path.join(PROJ, "outputs"))
    ap.add_argument("--logs", default=os.path.join(PROJ, "logs"))
    ap.add_argument("--slurm", default=os.path.join(PROJ, "slurm"))
    ap.add_argument("--apply", action="store_true",
                    help="actually write RUNMETA.json/DONE.json (default: dry run)")
    ap.add_argument("--dry-run", action="store_true", default=True,
                    help="report only; the default (--apply overrides)")
    ap.add_argument("--strict-names", action="store_true",
                    help="only summary.json / raw.jsonl count (ignore legacy prefixed names)")
    ap.add_argument("--only", default=None,
                    help="substring filter on the run-dir name (debugging)")
    ap.add_argument("--report-json", default=None, help="write the per-dir report here")
    ap.add_argument("--overwrite", action="store_true",
                    help="rewrite existing RUNMETA.json/DONE.json (default: never)")
    args = ap.parse_args()
    apply_ = args.apply

    try:
        sys.path.insert(0, PROJ)
        from ds_common import git_commit
        gen_commit = git_commit()
    except Exception:
        gen_commit = None

    slurm_idx = index_slurm(args.slurm)
    log_texts, log_parsed = index_logs(args.logs)
    shortnames = model_shortnames(log_parsed)

    dirs = sorted(d for d in os.listdir(args.outputs)
                  if os.path.isdir(os.path.join(args.outputs, d)))
    if args.only:
        dirs = [d for d in dirs if args.only in d]

    stats = {"dirs": len(dirs), "would_write_runmeta": 0, "would_write_done": 0,
             "already_has_runmeta": 0, "already_has_done": 0, "with_git_commit": 0,
             "with_log": 0, "with_script": 0, "with_model": 0, "wrote": 0}
    by_status = {}
    report = []

    for d in dirs:
        p = os.path.join(args.outputs, d)
        files = sorted(os.listdir(p))
        payload = [f for f in files if f not in (RUNMETA_NAME, DONE_NAME)]
        status, meta, done, has_git = build(p, d, payload, args.strict_names,
                                            log_texts, log_parsed, slurm_idx, gen_commit,
                                            shortnames)
        by_status[status] = by_status.get(status, 0) + 1
        stats["with_git_commit"] += int(has_git)
        stats["with_log"] += int(bool(meta["fields"]["log_files"]["value"]))
        stats["with_script"] += int("script" in meta["fields"])
        stats["with_model"] += int("model" in meta["fields"])
        stats["with_model_from_dirname"] = stats.get("with_model_from_dirname", 0) + int(
            "model" not in meta["fields"] and "model_from_dirname" in meta["fields"])

        rp, dp = os.path.join(p, RUNMETA_NAME), os.path.join(p, DONE_NAME)
        need_r = args.overwrite or not os.path.exists(rp)
        need_d = args.overwrite or not os.path.exists(dp)
        stats["already_has_runmeta"] += int(os.path.exists(rp))
        stats["already_has_done"] += int(os.path.exists(dp))
        stats["would_write_runmeta"] += int(need_r)
        stats["would_write_done"] += int(need_d)

        if apply_:
            for path, rec, need in ((rp, meta, need_r), (dp, done, need_d)):
                if not need:
                    continue
                tmp = path + ".tmp"
                with open(tmp, "w") as fh:
                    json.dump(rec, fh, indent=2)
                    fh.write("\n")
                os.replace(tmp, path)
                stats["wrote"] += 1

        report.append({"run_id": d, "status": status,
                       "git_commit": (meta["fields"].get("git_commit") or {}).get("value"),
                       "script": (meta["fields"].get("script") or {}).get("value"),
                       "model": (meta["fields"].get("model") or {}).get("value"),
                       "n_logs": len(meta["fields"]["log_files"]["value"]),
                       "write_runmeta": need_r, "write_done": need_d})

    mode = "APPLY" if apply_ else "DRY-RUN (no files written; pass --apply to write)"
    print(f"backfill_runmeta.py [{mode}]  outputs={_rel(args.outputs)}")
    print(f"  run dirs scanned                : {stats['dirs']}")
    print(f"  would write RUNMETA.json        : {stats['would_write_runmeta']}"
          f"   (already present: {stats['already_has_runmeta']})")
    print(f"  would write DONE.json           : {stats['would_write_done']}"
          f"   (already present: {stats['already_has_done']})")
    print("  status breakdown                :")
    for k in ("reconstructed", "incomplete", "empty", "unknown"):
        if k in by_status:
            print(f"      {k:<14} {by_status[k]}")
    print(f"  matched to a log file           : {stats['with_log']}")
    print(f"  got a git commit from logs      : {stats['with_git_commit']}")
    print(f"  got a script from slurm wrapper : {stats['with_script']}")
    print(f"  got a model id from logs        : {stats['with_model']}")
    print(f"  model inferred from dir name    : {stats.get('with_model_from_dirname', 0)}")
    if apply_:
        print(f"  files written                   : {stats['wrote']}")

    if args.report_json:
        with open(args.report_json, "w") as fh:
            json.dump({"stats": stats, "by_status": by_status, "runs": report}, fh, indent=2)
        print(f"  report -> {_rel(args.report_json)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
