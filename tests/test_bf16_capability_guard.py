"""DCS-CSI-139: the bf16 compute-capability guard, and the compute_capability provenance field.

Both are S-119 / S-127(a) fixes that sat queued for a full working day because PR-CSI-003 and then
PR-CSI-005 made src/boombness/score_behavior.py's blob a VOID condition of a running experiment.

WHY THE GUARD EXISTS, and why a LOUD failure was not enough. On a Tesla V100 (sm_70) bfloat16 is
EMULATED. Norm-matched arms there wrote ZERO rows -- loud, and it still cost four wrong attributions
across S-113..S-121 before anyone printed the GPU column. But every NON-norm-matched V100 arm wrote
ALL its rows, silently, in emulated arithmetic. The silent case is the one this guard is for.
"""
import ast
import os
import re
import types

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SB = os.path.join(REPO, "src/boombness/score_behavior.py")
DSC = os.path.join(REPO, "doublespeak_causality/ds_common.py")


def _src(p):
    with open(p) as fh:
        return fh.read()


# --------------------------------------------------------------------------- guard placement
def test_the_guard_is_at_the_load_site_not_at_argparse():
    """A guard at argparse can be bypassed by any path that builds args itself. It must sit between
    the caller and dc.load_model, so no code path reaches the model without passing it."""
    s = _src(SB)
    assert "get_device_capability" in s, "no compute-capability check in score_behavior.py"
    gi = s.index("get_device_capability")
    li = s.index("dc.load_model(model_id")
    assert gi < li, "the capability check must precede the load"
    between = s[gi:li]
    assert "\ndef " not in between, "the guard and the load are in different functions"
    assert between.count("\n") < 40, "the guard is too far from the load site to be load-gating"


def test_the_guard_refuses_only_bfloat16_and_only_below_8_0():
    s = _src(SB)
    m = re.search(r'if args\.dtype == "bfloat16" and torch\.cuda\.is_available\(\):'
                  r'\s*\n\s*_cc = torch\.cuda\.get_device_capability\(0\)'
                  r'\s*\n\s*if _cc\[0\] < 8:', s)
    assert m, "guard is not the expected shape (bfloat16 AND cuda available AND major < 8)"
    tail = s[m.end():m.end() + 800]
    assert "SystemExit" in tail, "the guard must RAISE, not warn"


def test_the_guard_names_the_device_and_the_capability_in_its_message():
    """A refusal that does not say WHICH device and WHICH capability sends the reader back to the
    cluster to find out. S-119 cost four entries for want of a printed GPU column."""
    s = _src(SB)
    i = s.index("REFUSING: --dtype bfloat16")
    msg = s[i:i + 900]
    assert "get_device_name" in msg, "message must name the device"
    assert "%d.%d" in msg, "message must print the compute capability"
    for cite in ("S-037", "S-119"):
        assert cite in msg or cite in s[max(0, i - 900):i], "message must cite the prior entries"


# ------------------------------------------------------- the guard itself, EXECUTED, not restated
# REVIEW R10 MAJOR-9. The test that used to sit here was TAUTOLOGICAL: it re-implemented the
# predicate (`got = bool(dtype == "bfloat16" and cuda_available and cc[0] < 8)`) and never read
# score_behavior.py at all. The reviewer copied the function into /tmp, ran pytest with no repo
# present, and got 5 passed -- the guard could have been deleted outright and this file would still
# have been green. A test that cannot fail is not a test.
#
# What follows EXECUTES THE REAL GUARD. The `if` statement is located in score_behavior.py's own
# AST, the parsed node is compiled and run against a STUBBED torch and a stubbed `args`, and the
# outcome (SystemExit or not) is the assertion. Delete or weaken the guard in the source and these
# cases go red: there is no copy of the predicate here to keep them passing.


def _guard_node():
    """The parsed `if args.dtype == "bfloat16" ...` statement, straight out of the real source."""
    s = _src(SB)
    tree = ast.parse(s)
    hits = [n for n in ast.walk(tree)
            if isinstance(n, ast.If)
            and isinstance(n.test, ast.BoolOp)
            and "get_device_capability" in (ast.get_source_segment(s, n) or "")
            and (ast.get_source_segment(s, n) or "").startswith(
                'if args.dtype == "bfloat16" and torch.cuda.is_available():')]
    assert len(hits) == 1, (
        "expected EXACTLY ONE bfloat16 capability guard in %s, found %d -- the guard this test "
        "exercises is gone or duplicated" % (SB, len(hits)))
    return hits[0]


class _FakeCuda(object):
    def __init__(self, available, cc, name):
        self._available, self._cc, self._name = available, cc, name
        self.capability_reads = 0

    def is_available(self):
        return self._available

    def get_device_capability(self, idx):
        self.capability_reads += 1
        return self._cc

    def get_device_name(self, idx):
        return self._name


class _FakeTorch(object):
    def __init__(self, available, cc, name):
        self.cuda = _FakeCuda(available, cc, name)


def _run_guard(dtype, cc, cuda_available=True, name="FAKE DEVICE"):
    """Execute the real guard node with a stubbed torch. Returns the SystemExit message, or None."""
    node = _guard_node()
    mod = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(mod)
    code = compile(mod, SB, "exec")
    torch_stub = _FakeTorch(cuda_available, cc, name)
    ns = {"torch": torch_stub, "args": types.SimpleNamespace(dtype=dtype)}
    try:
        exec(code, ns)
    except SystemExit as e:
        return str(e)
    return None


@pytest.mark.parametrize("cc,dtype,refuses", [
    ((7, 0), "bfloat16", True),    # Tesla V100 -- the case that cost S-113..S-121
    ((8, 6), "bfloat16", False),   # RTX 3090
    ((8, 9), "bfloat16", False),   # L40S
    ((7, 0), "float16", False),    # deliberate fp16 on a V100 is allowed
    ((7, 5), "bfloat16", True),
    ((9, 0), "bfloat16", False),   # H100
    ((7, 0), "float32", False),
])
def test_the_real_guard_refuses_exactly_these_devices(cc, dtype, refuses):
    """THE BEHAVIOURAL TEST. The guard is taken from score_behavior.py's AST and RUN."""
    msg = _run_guard(dtype, cc)
    assert (msg is not None) is refuses, (
        "guard on cc=%s dtype=%s %s, expected %s"
        % (cc, dtype, "REFUSED" if msg else "allowed", "REFUSE" if refuses else "allow"))
    if refuses:
        assert "REFUSING" in msg and "bfloat16" in msg
        assert "FAKE DEVICE" in msg, "the refusal does not name the device it read"
        assert "%d.%d" % cc in msg, "the refusal does not print the capability it read"


def test_the_real_guard_does_not_touch_cuda_when_cuda_is_absent():
    """On a CPU box the guard must not even ask for a capability -- it would raise, and this runs
    at the load site of every run. (`torch.cuda.is_available()` is the short-circuit.)"""
    node = _guard_node()
    mod = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(mod)
    torch_stub = _FakeTorch(False, (7, 0), "NO GPU")
    ns = {"torch": torch_stub, "args": types.SimpleNamespace(dtype="bfloat16")}
    exec(compile(mod, SB, "exec"), ns)
    assert torch_stub.cuda.capability_reads == 0, \
        "the guard read the device capability on a machine with no CUDA"


def test_the_behavioural_test_is_not_reading_a_copy_of_the_predicate():
    """MUTATION PROOF for the test above: flipping the threshold in the PARSED node must flip the
    outcome. If the test were restating the predicate (the R10 MAJOR-9 defect) this would not."""
    s = _src(SB)
    node = _guard_node()
    inner = [n for n in node.body if isinstance(n, ast.If)]
    assert len(inner) == 1, "expected exactly one capability test inside the guard, found %d" % len(inner)
    inner = inner[0]
    # `if _cc[0] < 8:` -> `if _cc[0] < 0:`; an RTX 3090 (8,6) already fails 8, and now so does
    # nothing -- so a V100 that DID refuse must now be allowed through.
    assert isinstance(inner.test, ast.Compare) and isinstance(inner.test.comparators[0], ast.Constant)
    assert inner.test.comparators[0].value == 8, \
        "the capability threshold in the source is %r, not 8" % inner.test.comparators[0].value
    inner.test.comparators[0] = ast.Constant(value=0)
    mod = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(mod)
    ns = {"torch": _FakeTorch(True, (7, 0), "FAKE DEVICE"),
          "args": types.SimpleNamespace(dtype="bfloat16")}
    exec(compile(mod, SB, "exec"), ns)   # must NOT raise now
    # and unmutated, the same device is refused
    assert _run_guard("bfloat16", (7, 0)) is not None
    assert "get_device_capability" in s


def test_the_guard_is_absent_from_the_pre_fix_blob():
    """MUTATION PROOF: this test must be able to fail. The guard did not exist at blob e94258bd,
    which is what every arm in PR-CSI-003 and PR-CSI-005 ran under."""
    import subprocess
    old = subprocess.run(["git", "show", "e94258bd5fc44c70629e707b00504b7acac2a7b7"],
                         cwd=REPO, capture_output=True, text=True)
    if old.returncode != 0:
        pytest.skip("pre-fix blob not reachable in this checkout")
    assert "get_device_capability" not in old.stdout, \
        "the pre-fix blob already had the guard -- this test proves nothing"


# --------------------------------------------------------------------------- provenance field
def test_env_block_records_compute_capability():
    """S-127(a): compute capability was recorded in ZERO of 305 run directories, while being the
    field PR-CSI-003's VOID condition depends on. It had to be inferred from the gpu model string."""
    s = _src(DSC)
    assert '"compute_capability": compute_capability,' in s, \
        "the env/provenance block does not emit compute_capability"
    assert "torch.cuda.get_device_capability(0)" in s, "it is not actually measured"
    tree = ast.parse(s)
    assert tree is not None


def test_compute_capability_actually_REACHES_runmeta_not_just_env_metadata():
    """THE TEST I SHOULD HAVE WRITTEN FIRST. RUNMETA.json is built from an EXPLICIT field list that
    copies selected keys out of env_metadata(), not from env wholesale. The first version of this
    fix added compute_capability to env_metadata() ONLY, so the field never reached the artifact --
    and the anchor arm (job 913314) came back with it ABSENT on a machine whose own RUNMETA said
    "NVIDIA GeForce RTX 3090". A field in the producer that never lands in the artifact is worse
    than no field: `m.get("compute_capability")` returns None either way, so "never written" is
    indistinguishable from "measured as None"."""
    s = _src(DSC)
    assert '"compute_capability": env.get("compute_capability"),' in s, \
        "compute_capability is not copied into the RUNMETA field list"
    # and it must sit in the same record literal as the gpu field it belongs beside
    i = s.index('"gpu": env.get("gpu"),')
    j = s.index('"compute_capability": env.get("compute_capability"),')
    assert 0 < j - i < 900, "the RUNMETA copy is not adjacent to its gpu field"


def test_every_env_key_that_matters_is_copied_into_runmeta():
    """Generalises the bug: any provenance key added to env_metadata() and not to the RUNMETA field
    list is silently invisible. Guards the fields a VOID condition can depend on."""
    s = _src(DSC)
    for key in ("gpu", "compute_capability", "cuda_available", "torch", "git_commit", "hostname"):
        assert '"%s": env.get("%s"),' % (key, key) in s, \
            "env key %r is not copied into RUNMETA -- it would be invisible in every artifact" % key


def test_compute_capability_is_none_without_cuda_and_never_raises():
    """The env block is provenance: it must degrade to None on a CPU box, never explode. Every
    capture in it is inside a try/except for that reason."""
    s = _src(DSC)
    i = s.index("compute_capability = None")
    j = s.index('"compute_capability": compute_capability,')
    block = s[i:j]
    assert "try:" in block and "except Exception:" in block, \
        "the capability capture is not inside the try/except that protects the rest of the block"
    assert "if cuda_avail:" in block, "capability is read without first checking cuda_avail"
