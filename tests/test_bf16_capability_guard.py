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


@pytest.mark.parametrize("cc,dtype,refuses", [
    ((7, 0), "bfloat16", True),    # Tesla V100 -- the case that cost S-113..S-121
    ((8, 6), "bfloat16", False),   # RTX 3090
    ((8, 9), "bfloat16", False),   # L40S
    ((7, 0), "float16", False),    # deliberate fp16 on a V100 is allowed
    ((7, 5), "bfloat16", True),
])
def test_guard_predicate_truth_table(cc, dtype, refuses):
    """The predicate itself, evaluated exactly as written, over the devices this project has used."""
    cuda_available = True
    got = bool(dtype == "bfloat16" and cuda_available and cc[0] < 8)
    assert got is refuses


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
