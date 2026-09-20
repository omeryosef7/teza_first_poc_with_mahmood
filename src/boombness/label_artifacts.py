"""label_artifacts.py — give every CITED artifact a label a reader can act on.

WHY. Plan §20 item 6 says "do not leave undocumented scripts or unlabeled outputs". The scripts were
verified (126/126 carry a substantive module docstring). The OUTPUTS were never checked, and 26 of the
55 artifacts cited in the deliverables carried no statement of what question they answer and/or no
provenance block. A reader who follows a citation lands on a wall of numbers with no way to tell what
it is for.

WHAT IT DOES, AND WHAT IT REFUSES TO DO. It ADDS keys prefixed with `_` and never touches an existing
key, so no published value can change -- adding a key cannot alter a number, and rewriting one could.
The label is not invented: it is the SENTENCE FROM THE REPORT THAT CITES THE ARTIFACT, so the artifact
carries the claim it is actually used for rather than a description I made up afterwards. Where the
citation is uninformative that is visible in the label, which is itself worth knowing.

IDEMPOTENT: re-running overwrites only the `_` keys it owns.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys

DELIVERABLES = ["reports/boombness_objective_sprint_report.md",
                "reports/boombness_objective_sprint_short_update.md"]


def citations(text, base):
    """Sentences in `text` that name `base`."""
    out = []
    for m in re.finditer(re.escape(base), text):
        lo = max(0, text.rfind("\n\n", 0, m.start()))
        hi = text.find("\n\n", m.end())
        blk = text[lo:hi if hi > 0 else len(text)].strip()
        # the sentence containing the citation
        for s in re.split(r"(?<=[.!?])\s+", blk.replace("\n", " ")):
            if base in s:
                out.append(re.sub(r"\s+", " ", s).strip())
                break
    return out


def _atomic_json_dump(obj, path, **kw):
    """Atomic, VERIFIED JSON write. Fix for sprint entry S-124.

    Replaces `json.dump(x, open(p, "w"), ...)`, whose handle is never closed: `open` truncates the
    destination immediately and the buffered bytes are flushed only in the GC finaliser, where
    CPython PRINTS and then SWALLOWS an EDQUOT. A full quota therefore produced a 0-byte file at a
    real artifact name, with "wrote <path>" on stdout and exit status 0 -- indistinguishable from a
    finished report. Temp file + fsync + size check + re-parse + os.replace makes the write ATOMIC
    as well as checked: a half-written file never appears at the real name, and whatever was there
    before survives a failure. On any error this RAISES, naming the path and the byte count.
    """
    import tempfile                        # local: keeps this helper drop-in and import-order-free
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_atomic_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, **kw)
            fh.flush()
            os.fsync(fh.fileno())          # EDQUOT surfaces HERE, not in a GC finaliser
        n = os.path.getsize(tmp)
        if n == 0:
            raise OSError("temp file is 0 bytes after a flush+fsync that reported success")
        with open(tmp, "r", encoding="utf-8") as fh:
            json.load(fh)                  # a truncated write does not re-parse
        try:
            mode = os.stat(path).st_mode & 0o7777   # keep the artifact's existing permissions:
        except OSError:                             # mkstemp makes the temp file 0600 and
            mode = 0o644                            # os.replace would carry that onto the report
        os.chmod(tmp, mode)
        os.replace(tmp, path)              # atomic within the directory
    except Exception as e:
        try:
            n = os.path.getsize(tmp)
        except OSError:
            n = -1
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise OSError("atomic_json_dump FAILED for %s -- %d bytes reached the temp file; the "
                      "destination is UNCHANGED (never truncated). Cause: %r" % (path, n, e)) from e
    return os.path.getsize(path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    docs = "\n\n".join(io.open(f, encoding="utf-8").read() for f in DELIVERABLES)
    tracked = subprocess.run(["git", "ls-files", "outputs/boombness/*.json"],
                             capture_output=True, text=True).stdout.split()
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                         text=True).stdout.strip()
    LABEL = {"question", "why", "what", "reading", "note", "purpose", "label"}
    touched, skipped = 0, 0
    for path in tracked:
        base = os.path.basename(path)
        if base not in docs:
            continue
        try:
            d = json.load(open(path))
        except Exception:
            print(f"  SKIP {base}: unparseable")
            skipped += 1
            continue
        if not isinstance(d, dict):
            print(f"  SKIP {base}: top level is {type(d).__name__}, not an object")
            skipped += 1
            continue
        keys = set(d)
        has_label = bool(keys & LABEL) or any(k.isupper() for k in keys)
        has_prov = "provenance" in keys
        if has_label and has_prov:
            continue
        cites = citations(docs, base)
        add = {}
        if not has_label:
            add["_cited_as"] = (cites[0][:400] if cites else
                                "cited in a deliverable, but the citing sentence names no claim")
            add["_label_note"] = ("added by label_artifacts.py: this is the REPORT'S OWN citing "
                                  "sentence, not a description written after the fact")
        if not has_prov:
            add["_provenance_added"] = {"by": "label_artifacts.py", "git_commit": sha,
                                        "note": "this artifact predates the provenance convention; "
                                                "the commit here is when the label was added, NOT "
                                                "when the artifact was produced"}
        if args.dry_run:
            print(f"  would label {base}: {list(add)}")
        else:
            d.update(add)
            _atomic_json_dump(d, path, indent=2, ensure_ascii=False)
            print(f"  labelled {base}")
        touched += 1
    print(f"\n[label-artifacts] {touched} cited artifact(s) {'would be ' if args.dry_run else ''}"
          f"labelled, {skipped} skipped (not JSON objects)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
