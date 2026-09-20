#!/usr/bin/env python3
"""A report write must never leave a 0-byte file at a real artifact name. Regression test for S-124.

*** WHY THIS FILE EXISTS. ***
On 2026-09-20 the disk quota was exactly full. The frozen PR-CSI-002 read ran to completion,
printed `wrote reports/...` for both of its output files and exited 0. Both files were 0 BYTES.

The cause was the idiom `json.dump(out, open(path, "w"), indent=1)`, which both analysers used.
The handle is never closed: `open` truncates the destination immediately, the buffered bytes are
flushed only when the file object is garbage-collected, and an exception raised inside a
finaliser -- EDQUOT here -- is PRINTED by CPython and then SWALLOWED. So the failure could not
reach the exit status, and what was left behind was a 0-byte file at a preregistered artifact
name, indistinguishable from a finished report. See sprint entry S-124.

WHAT THIS FILE PINS DOWN. It drives the REAL persistence helpers -- it does not re-implement
them -- and asserts two properties for EACH of the two independent analysis paths:

  (a) a normal write produces a non-empty file that re-parses as the object that went in;
  (b) when the underlying write raises OSError(errno.EDQUOT) MID-WAY, the helper RAISES, and the
      destination path is left either ABSENT or holding its PREVIOUS content -- never truncated
      to 0 bytes, and never holding a half-written report.

Property (b) is the strong one, and it is why the fix is temp-file + fsync + verify + os.replace
rather than merely a with-block: a with-block would surface the error but the destination would
already have been truncated by `open`.

BOTH PATHS ARE TESTED SEPARATELY AND ON PURPOSE. dcs_csi_subspace_analyze.py and
dcs_csi_rederive_subspace.py share no analysis code (DCS-CSI-085) and each carries its own copy of
the helper for that reason. Two copies is two places to regress, so both are checked here.
"""
import errno
import importlib.util
import json
import os
import sys
import types

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (module alias, path relative to the repo root). Both analysers, plus the shared-nothing
# re-derivation module that the primary analyser loads, so the swept copy of the helper is
# exercised too.
PATHS = [
    ("s124_subspace", "scripts/dcs_csi_subspace_analyze.py"),
    ("s124_rederive", "scripts/dcs_csi_rederive_subspace.py"),
    ("s124_rederive_patch", "scripts/dcs_csi_rederive_patch.py"),
]


def _load(alias, rel):
    """Load by path, the way the sprint's own scripts do.

    sys.path carries `scripts/` because these modules import their siblings by bare name.
    """
    sp = os.path.join(REPO, "scripts")
    if sp not in sys.path:
        sys.path.insert(0, sp)
    spec = importlib.util.spec_from_file_location(alias, os.path.join(REPO, rel))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[alias] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module", params=PATHS, ids=[p[1] for p in PATHS])
def mod(request):
    alias, rel = request.param
    m = _load(alias, rel)
    assert hasattr(m, "_atomic_json_dump"), (
        "%s has no _atomic_json_dump -- either the S-124 fix was reverted, or a stale "
        "__pycache__ entry is being executed instead of the file on disk (S-120c). Module "
        "__file__ is %s" % (rel, getattr(m, "__file__", "?")))
    return m


def _payload():
    return {"VERDICT": "INCONCLUSIVE", "ranks": {"all": 1, "shuffled_only": 1},
            "candidate_minus_KO": [0.1, -0.2, 3.0], "nested": {"a": {"b": [1, 2, 3]}}}


def _leftovers(d):
    return [f for f in os.listdir(d) if f.startswith(".tmp_atomic_")]


# ---------------------------------------------------------------- (a) the normal write

def test_normal_write_is_nonempty_and_reparses(mod, tmp_path):
    dst = str(tmp_path / "REPORT.json")
    obj = _payload()
    n = mod._atomic_json_dump(obj, dst, indent=1)
    assert os.path.exists(dst)
    assert os.path.getsize(dst) > 0, "the exact failure mode of S-124: a 0-byte artifact"
    assert n == os.path.getsize(dst), "the helper must return the VERIFIED byte count"
    with open(dst, encoding="utf-8") as fh:
        assert json.load(fh) == obj
    assert _leftovers(str(tmp_path)) == [], "temp file left behind on the success path"


def test_normal_write_replaces_previous_content(mod, tmp_path):
    dst = str(tmp_path / "REPORT.json")
    mod._atomic_json_dump({"old": True}, dst, indent=1)
    mod._atomic_json_dump({"new": True}, dst, indent=1)
    with open(dst, encoding="utf-8") as fh:
        assert json.load(fh) == {"new": True}


# ---------------------------------------------------------------- (b) EDQUOT mid-write

class _PartialThenEDQUOT:
    """`json.dump` that writes some bytes and THEN fails, which is what a full quota looks like.

    Patched into the module's own `json` binding rather than into the global json module, so the
    fault is confined to the helper under test.
    """

    def __init__(self, nbytes=4096):
        self.nbytes = nbytes

    def dump(self, obj, fh, **kw):
        fh.write("x" * self.nbytes)
        raise OSError(errno.EDQUOT, os.strerror(errno.EDQUOT))

    def load(self, fh):
        return json.load(fh)

    def dumps(self, *a, **k):
        return json.dumps(*a, **k)


def _with_broken_json(mod, broken):
    real = mod.json
    mod.json = broken
    return real


def test_edquot_midwrite_raises_and_leaves_destination_absent(mod, tmp_path):
    dst = str(tmp_path / "REPORT.json")
    real = _with_broken_json(mod, _PartialThenEDQUOT())
    try:
        with pytest.raises(OSError) as ei:
            mod._atomic_json_dump(_payload(), dst, indent=1)
    finally:
        mod.json = real
    assert "atomic_json_dump FAILED" in str(ei.value)
    assert dst in str(ei.value), "the error must name the path"
    assert not os.path.exists(dst), "a failed write must not create the artifact at all"
    assert _leftovers(str(tmp_path)) == [], "temp file left behind on the failure path"


def test_edquot_midwrite_preserves_previous_content(mod, tmp_path):
    dst = str(tmp_path / "REPORT.json")
    mod._atomic_json_dump({"previous": "report"}, dst, indent=1)
    before = open(dst, "rb").read()
    assert len(before) > 0

    real = _with_broken_json(mod, _PartialThenEDQUOT())
    try:
        with pytest.raises(OSError):
            mod._atomic_json_dump(_payload(), dst, indent=1)
    finally:
        mod.json = real

    after = open(dst, "rb").read()
    assert len(after) > 0, "S-124 EXACTLY: the artifact was truncated to 0 bytes by a failed write"
    assert after == before, "a failed write must leave the PREVIOUS report byte-identical"
    assert json.loads(after.decode()) == {"previous": "report"}
    assert _leftovers(str(tmp_path)) == []


def test_edquot_at_fsync_raises_and_preserves_previous_content(mod, tmp_path, monkeypatch):
    """The real S-124 failure surfaced at FLUSH, not inside json.dump. Pin that path too."""
    dst = str(tmp_path / "REPORT.json")
    mod._atomic_json_dump({"previous": "report"}, dst, indent=1)
    before = open(dst, "rb").read()

    def boom(fd):
        raise OSError(errno.EDQUOT, os.strerror(errno.EDQUOT))

    monkeypatch.setattr(mod.os, "fsync", boom)
    with pytest.raises(OSError) as ei:
        mod._atomic_json_dump(_payload(), dst, indent=1)
    assert "atomic_json_dump FAILED" in str(ei.value)
    assert open(dst, "rb").read() == before
    assert _leftovers(str(tmp_path)) == []


def test_zero_byte_temp_file_is_refused(mod, tmp_path):
    """Belt and braces: if a write silently produces 0 bytes, the helper must still refuse."""
    dst = str(tmp_path / "REPORT.json")

    class _WritesNothing:
        def dump(self, obj, fh, **kw):
            pass

        def load(self, fh):
            return json.load(fh)

    real = _with_broken_json(mod, _WritesNothing())
    try:
        with pytest.raises(OSError) as ei:
            mod._atomic_json_dump(_payload(), dst, indent=1)
    finally:
        mod.json = real
    assert "0 bytes" in str(ei.value)
    assert not os.path.exists(dst)


# ---------------------------------------------------------------- the idiom must not come back

def _unclosed_write_sites(rel):
    """Every `json.dump(x, open(p, "w"))` and `open(p, "w").write(...)` in a file, by AST.

    AST and not a regex ON PURPOSE. The first version of this check was a regex and it fired on
    the helper's own DOCSTRING, which quotes the broken idiom in order to explain it. A detector
    that cannot tell code from prose would have to be silenced, and a silenced detector is how the
    idiom comes back.
    """
    import ast
    tree = ast.parse(open(os.path.join(REPO, rel), "rb").read())

    def writes(n):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "open"):
            return False
        m = n.args[1].value if (len(n.args) > 1 and isinstance(n.args[1], ast.Constant)) else "r"
        return isinstance(m, str) and any(c in m for c in ("w", "a", "x"))

    safe = {id(it.context_expr) for n in ast.walk(tree)
            if isinstance(n, (ast.With, ast.AsyncWith)) for it in n.items}
    bound = {id(n.value) for n in ast.walk(tree) if isinstance(n, ast.Assign) and writes(n.value)}
    return ["%s:%d" % (rel, n.lineno) for n in ast.walk(tree)
            if writes(n) and id(n) not in safe and id(n) not in bound]


def test_the_broken_idiom_is_gone_from_both_analysers():
    """An unclosed write handle in either analyser IS the S-124 bug, by construction."""
    bad = [s for _, rel in PATHS[:2] for s in _unclosed_write_sites(rel)]
    assert bad == [], "the unclosed-handle write idiom is back at: %s" % bad
