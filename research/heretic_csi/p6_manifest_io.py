#!/usr/bin/env python3
"""Atomic, locked read-modify-write of outputs/heretic_csi/p6/stage0_<cw>.json (review #8 item 3). Every writer
(p6_write_manifest.py, p6_g2.py, p6_backfill_manifest.py, p6_axisfit.slurm via `python p6_manifest_io.py set ...`)
goes through update(): exclusive fcntl lock on <man>.lock, read, modify, write to a temp file in the same dir, fsync,
os.replace (atomic on POSIX). CLI: p6_manifest_io.py set <man> <key> <json-value>"""
import fcntl, json, os, sys, tempfile


def update(man, fn):
    os.makedirs(os.path.dirname(os.path.abspath(man)), exist_ok=True)
    with open(man + ".lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        cur = json.load(open(man)) if os.path.exists(man) else {}
        new = fn(cur)
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(man)), prefix=".manifest.")
        with os.fdopen(fd, "w") as f:
            json.dump(new, f, indent=1); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, man)
        return new


if __name__ == "__main__":
    if len(sys.argv) != 5 or sys.argv[1] != "set":
        sys.exit("usage: p6_manifest_io.py set <man> <key> <json-value>")
    _, _, man, key, val = sys.argv
    update(man, lambda m: {**m, key: json.loads(val)})
