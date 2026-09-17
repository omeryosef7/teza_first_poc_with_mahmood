"""S-106: the recorded `bases[*].sha16` must hash THE BYTES SAVED, not the pre-downcast buffer.

The defect these lock down. `dcs_csi_axis.py` recorded `sha16(B)` off the float64 fit buffer and
then saved `B.to(torch.float32)`. `torch.linalg.solve` is not bit-reproducible across runs or
thread counts, so two builds of the SAME axis at the SAME layer differed in the float64 tail while
their saved float32 tensors were BITWISE IDENTICAL -- and the artifact recorded two different
hashes for one axis. Demonstrated on the real files: configs/dcs_csi_axis_basket_behavioral.json
sha16 0c397a778db933ba vs configs/dcs_csi_axis_basket_behavioral_shuf24.json fad8b030ae93976e,
both selected_layer 18, torch.equal(saved tensors) True, max abs diff 0.000e+00. That made a
"differing sha16" look like evidence the axis had changed, and S-103 leaned on exactly that
inference.

These tests assert BOTH halves, because a hash that is merely stable is as useless as one that is
merely noisy -- it has to be stable for the SAME saved tensor and it has to MOVE for a different
one:

  * equal saved tensors  => EQUAL recorded hash   (this is the half the old code failed), and
  * different saved tensors => DIFFERENT recorded hash (the half a constant would break), and
  * the recorded hash recomputes from the tensor READ BACK OUT of the .pt, so it is a property of
    the file on disk and not of any in-memory intermediate, and
  * the OLD ordering, reproduced here explicitly, really does fail the first half -- otherwise
    this file could pass against the bug it exists to catch.
"""
import hashlib
import importlib.util
import os
import sys

import pytest
import torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, relpath))
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


@pytest.fixture()
def axis():
    return _load("csi_axis_s106", "scripts/dcs_csi_axis.py")


def _pair_equal_in_float32():
    """Two float64 axes that differ ONLY below float32 resolution: the non-reproducible tail.

    This is the shape of the real artifact pair -- a solve that landed on a slightly different
    float64 answer for the same problem -- reproduced deterministically instead of by racing
    threads.
    """
    a = torch.linspace(-1.0, 1.0, 64, dtype=torch.float64).unsqueeze(0)
    b = a + 1e-12 * torch.ones_like(a)          # far below float32 eps at this magnitude
    assert not torch.equal(a, b), "the fixture must differ in float64, or it tests nothing"
    assert torch.equal(a.to(torch.float32), b.to(torch.float32)), \
        "the fixture must collapse to the same float32, or it tests nothing"
    return {"cand_rank1": a}, {"cand_rank1": b}


def _build(axis, bases, tmp_path, name):
    """Run the REAL record-and-save path and return (recorded meta, reloaded blob, path)."""
    out = {"schema": "dcs_csi_axis/1", "selected_layer": 18}
    p = str(tmp_path / ("%s.pt" % name))
    axis.save_bases(bases, out, p)
    return out, torch.load(p, map_location="cpu", weights_only=False), p


def test_same_saved_tensor_records_the_same_hash(axis, tmp_path):
    """THE regression: sub-float32 noise must NOT move the recorded hash."""
    ba, bb = _pair_equal_in_float32()
    oa, pa, _ = _build(axis, ba, tmp_path, "a")
    ob, pb, _ = _build(axis, bb, tmp_path, "b")

    assert torch.equal(pa["bases"]["cand_rank1"], pb["bases"]["cand_rank1"]), \
        "precondition: the two saved tensors are bitwise identical"
    assert oa["bases"]["cand_rank1"]["sha16"] == ob["bases"]["cand_rank1"]["sha16"], \
        "identical saved tensors recorded different hashes -- S-106 is back"


def test_the_old_ordering_would_have_failed_this(axis, tmp_path):
    """The other side of the same coin: hashing the PRE-DOWNCAST buffer splits one axis in two.

    Without this, the test above could pass for the wrong reason (e.g. a fixture whose float64
    tails happened to agree) and would not be a regression test for anything.
    """
    ba, bb = _pair_equal_in_float32()
    old = lambda t: hashlib.sha256(
        t.to(torch.float64).contiguous().numpy().tobytes()).hexdigest()[:16]

    assert old(ba["cand_rank1"]) != old(bb["cand_rank1"]), \
        "the old pre-downcast hash must be the thing that differs, else the fixture is wrong"
    oa, _, _ = _build(axis, ba, tmp_path, "a")
    assert oa["bases"]["cand_rank1"]["sha16"] != old(ba["cand_rank1"]), \
        "the new recorded hash must not be the old float64 value"


def test_a_genuinely_different_axis_records_a_different_hash(axis, tmp_path):
    """The half a hardcoded constant, or a hash of the shape alone, would break.

    The perturbation is one ULP-scale-visible change in a single coordinate: enough to survive the
    float32 downcast, and nothing else about the basis moves.
    """
    ba, _ = _pair_equal_in_float32()
    bc = {"cand_rank1": ba["cand_rank1"].clone()}
    bc["cand_rank1"][0, 7] += 1e-3
    assert not torch.equal(ba["cand_rank1"].to(torch.float32),
                           bc["cand_rank1"].to(torch.float32)), "precondition: differs in float32"

    oa, _, _ = _build(axis, ba, tmp_path, "a")
    oc, _, _ = _build(axis, bc, tmp_path, "c")
    assert oa["bases"]["cand_rank1"]["sha16"] != oc["bases"]["cand_rank1"]["sha16"], \
        "a really different axis recorded the same hash -- the hash is inert"


def test_the_recorded_hash_recomputes_from_the_file_on_disk(axis, tmp_path):
    """The hash must be verifiable against the .pt by a third party, with no access to the fit.

    This is what makes a differing hash mean something: anyone holding the artifact can recompute
    it. It also pins the recorded rank to the SAVED tensor's shape.
    """
    ba, _ = _pair_equal_in_float32()
    ba["cand_pls3"] = torch.randn(3, 64, dtype=torch.float64)
    out, blob, _ = _build(axis, ba, tmp_path, "a")

    for k, B in blob["bases"].items():
        assert B.dtype is torch.float32, "the artifact persists float32; the hash must match it"
        assert axis.sha16(B) == out["bases"][k]["sha16"], \
            "%s: recorded hash does not recompute from the saved tensor" % k
        assert out["bases"][k]["rank"] == int(B.shape[0])
    assert blob["meta"]["bases_sha16_of"] == "saved_float32_tensor_bytes", \
        "new artifacts must declare what the hash is of, so old float64 hashes are distinguishable"


def test_saved_tensors_are_byte_identical_to_the_old_save_path(axis, tmp_path):
    """The fix is metadata only: `save_bases` must persist exactly what the old two lines did."""
    ba, _ = _pair_equal_in_float32()
    ba["ctrl_random0"] = torch.randn(1, 64, dtype=torch.float64)
    ba["ctrl_random_r2_0"] = torch.linalg.qr(
        torch.randn(64, 2, dtype=torch.float64))[0].T.contiguous()

    _, blob, _ = _build(axis, ba, tmp_path, "new")
    ref = str(tmp_path / "old.pt")
    torch.save({"meta": {}, "bases": {k: B.to(torch.float32) for k, B in ba.items()}}, ref)
    old_blob = torch.load(ref, map_location="cpu", weights_only=False)

    assert set(blob["bases"]) == set(old_blob["bases"])
    for k in old_blob["bases"]:
        new_t, old_t = blob["bases"][k], old_blob["bases"][k]
        assert new_t.dtype is old_t.dtype and new_t.shape == old_t.shape
        assert new_t.contiguous().numpy().tobytes() == old_t.contiguous().numpy().tobytes(), \
            "%s: the fix moved a saved tensor -- it must not" % k
