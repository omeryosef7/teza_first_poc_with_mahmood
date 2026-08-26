"""Every committed argsfile must still be the one that produced its artifact.

WHY (2026-08-26). The reproduction manifest points at `runargs/*/*.txt` for every GPU arm. Those
files are the ONLY record of how an arm was invoked, and nothing stopped one from being edited after
its job was submitted -- at which point the manifest would name a command that never ran, silently
and forever. `RUNMETA.json` records the run's real `argv`, so the two can be compared.

Measured at the time of writing: 38 argsfiles, 38 matching runs, 0 differences, 0 orphans.

Skips cleanly when `outputs/` is absent (it is gitignored, so a fresh clone has no run dirs); this
guards a working tree, not a checkout.
"""

from __future__ import annotations

import glob
import json
import os
import shlex

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _pairs():
    out = []
    for f in sorted(glob.glob(os.path.join(REPO, "runargs", "*", "*.txt"))):
        toks = shlex.split(open(f).read().strip())
        if "--tag" not in toks:
            continue                      # analysis argsfiles carry no --tag
        tag = toks[toks.index("--tag") + 1]
        dirs = sorted(glob.glob(os.path.join(
            REPO, "outputs", "boombness", "score_behavior", f"{tag}_2026*")))
        # IN-FLIGHT RUNS ARE SKIPPED, NOT FAILED. A run dir appears as soon as the job starts, but
        # RUNMETA.json is written at the end, so comparing an unfinished run reports a mismatch that
        # is really "not written yet". Measured 2026-08-26: this guard failed spuriously during a
        # full-suite run while the p13 arms were generating, and passed on its own minutes later.
        # A guard that cries wolf whenever a sweep is running is a guard that gets ignored.
        dirs = [d for d in dirs if os.path.exists(os.path.join(d, "DONE.json"))]
        if dirs:
            out.append((os.path.relpath(f, REPO), toks, dirs[-1]))
    return out


def test_every_argsfile_matches_the_argv_its_run_used():
    pairs = _pairs()
    if not pairs:
        pytest.skip("no run directories on disk (outputs/ is gitignored)")
    bad = []
    for rel, toks, d in pairs:
        meta = os.path.join(d, "RUNMETA.json")
        if not os.path.exists(meta):
            bad.append((rel, "no RUNMETA.json"))
            continue
        argv = json.load(open(meta)).get("argv") or []
        ran = list(argv[1:])              # drop the script path
        if sorted(ran) != sorted(toks):
            only_file = sorted(set(toks) - set(ran))[:5]
            only_run = sorted(set(ran) - set(toks))[:5]
            bad.append((rel, f"only-in-file={only_file} only-in-run={only_run}"))
    assert not bad, (
        "committed argsfiles no longer match the runs they name — the manifest would point at a "
        f"command that never ran:\n" + "\n".join(f"  {r}: {w}" for r, w in bad))


def test_the_check_is_not_vacuous():
    """A guard that silently matches nothing would pass forever."""
    pairs = _pairs()
    if not pairs:
        pytest.skip("no run directories on disk")
    assert len(pairs) >= 20, f"only {len(pairs)} argsfile/run pairs found; the guard has gone blind"
