"""Torch-free unit tests for scripts/phase_f_probe_driver.py (Phase-F1.3 driver).

All fixtures are SYNTHETIC and built inside a tmp dir: a hand-written
``*_spans.jsonl`` carrying structural token ranges plus DECOY ``goal`` /
``preview`` sentinels, and a deterministic ``fake_forward_fn`` returning a small
numpy attention array. No text, no model, no torch, no real spans files. Every
asserted number is hand-computed here so the driver is pinned exactly.
"""

import csv
import json
import os
import sys

import numpy as np
import pytest

# Make the repo root importable so the driver's ``from scripts.… import …`` and
# our ``import scripts.phase_f_probe_driver`` both resolve (namespace package).
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import scripts.phase_f_probe_driver as drv  # noqa: E402

# Sentinel harmful-text strings that MUST NOT survive load_records.
_DECOY_GOAL = "DECOY_HARMFUL_GOAL_SENTINEL"
_DECOY_PREVIEW = "DECOY_HARMFUL_PREVIEW_SENTINEL"


def _mk_instance(cs, ce, ts, te):
    """A span instance carrying the four indices PLUS a decoy preview sentinel."""
    return {
        "char_start": cs,
        "char_end": ce,
        "tok_start": ts,
        "tok_end": te,
        "preview": _DECOY_PREVIEW,
    }


def _mk_record(task_id, is_success, n_tokens, spans, with_goal=True):
    rec = {
        "task_id": task_id,
        "is_success": is_success,
        "n_tokens": n_tokens,
        "target_model": "synthetic/Model",
        "judge_score": 0.0,
        "spans": spans,
    }
    if with_goal:
        rec["goal"] = _DECOY_GOAL
    return rec


def _record_with_cue():
    """Record whose final_answer_cue covers tokens [4,6) and harmful_instr [0,2)."""
    spans = {
        "benign_puzzle_scaffold": {
            "located": True,
            "instances": [_mk_instance(0, 10, 0, 4)],
        },
        "harmful_instruction": {
            "located": True,
            "instances": [_mk_instance(10, 15, 0, 2)],
        },
        "final_answer_cue": {
            "located": True,
            "instances": [_mk_instance(20, 30, 4, 6)],
        },
        "injected_reasoning": {"located": False, "instances": []},
    }
    return _mk_record("task_A", True, 6, spans)


def _record_no_cue():
    """Record with NO located final_answer_cue → query fallback fires."""
    spans = {
        "benign_puzzle_scaffold": {
            "located": True,
            "instances": [_mk_instance(0, 10, 0, 4)],
        },
        "harmful_instruction": {"located": False, "instances": []},
        "final_answer_cue": {"located": False, "instances": []},
        "injected_reasoning": {
            "located": True,
            "instances": [_mk_instance(5, 8, 1, 3)],
        },
    }
    return _mk_record("task_B", False, 40, spans)


def _write_jsonl(tmp_path, records):
    p = os.path.join(str(tmp_path), "synthetic_spans.jsonl")
    with open(p, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return p


def fake_forward_fn(record):
    """Deterministic [n_layers=1, n_heads=1, n_q=6, n_k=6] attention array.

    Each query row q gets uniform mass 1/6 over all 6 keys, so normalized span
    mass into a k-width span is exactly k/6 regardless of the query row chosen.
    """
    return np.full((1, 1, 6, 6), 1.0 / 6.0, dtype=np.float64)


# --------------------------------------------------------------------------- #
# load_records sanitization
# --------------------------------------------------------------------------- #
def test_load_records_drops_goal_and_preview(tmp_path):
    path = _write_jsonl(tmp_path, [_record_with_cue(), _record_no_cue()])
    records = drv.load_records(path)
    assert len(records) == 2

    blob = json.dumps(records)
    # Neither harmful sentinel may survive anywhere in the loaded structure.
    assert _DECOY_GOAL not in blob
    assert _DECOY_PREVIEW not in blob

    for rec in records:
        assert "goal" not in rec
        assert set(rec.keys()) == {
            "is_success",
            "n_tokens",
            "target_model",
            "task_id",
            "conversation_id",
            "attack_iteration",
            "spans",
        }
        for comp in rec["spans"].values():
            assert set(comp.keys()) == {"located", "instances"}
            for inst in comp["instances"]:
                assert set(inst.keys()) == {
                    "char_start",
                    "char_end",
                    "tok_start",
                    "tok_end",
                }
                assert "preview" not in inst


# --------------------------------------------------------------------------- #
# query_positions_for_record
# --------------------------------------------------------------------------- #
def test_query_positions_uses_cue_union():
    rec = _record_with_cue()
    # final_answer_cue covers [4,6) → {4,5}.
    assert drv.query_positions_for_record(rec) == [4, 5]


def test_query_positions_fallback_last_32():
    rec = _record_no_cue()  # n_tokens=40, no located cue.
    assert drv.query_positions_for_record(rec) == list(range(8, 40))


def test_query_positions_fallback_small_n():
    spans = {"final_answer_cue": {"located": False, "instances": []}}
    rec = _mk_record("t", True, 5, spans)
    # max(0, 5-32)=0 → range(0,5).
    assert drv.query_positions_for_record(rec) == [0, 1, 2, 3, 4]


# --------------------------------------------------------------------------- #
# span_ranges_for_record
# --------------------------------------------------------------------------- #
def test_span_ranges_default_components():
    rec = _record_with_cue()
    ranges = drv.span_ranges_for_record(rec)
    assert set(ranges.keys()) == set(drv.DEFAULT_COMPONENTS)
    assert ranges["benign_puzzle_scaffold"] == [(0, 4)]
    assert ranges["harmful_instruction"] == [(0, 2)]
    assert ranges["final_answer_cue"] == [(4, 6)]
    assert ranges["injected_reasoning"] == []  # unlocated → empty


# --------------------------------------------------------------------------- #
# build_per_record
# --------------------------------------------------------------------------- #
def test_build_per_record_shapes_and_masses():
    recs = [_record_with_cue()]
    per = drv.build_per_record(recs, fake_forward_fn)
    assert len(per) == 1
    entry = per[0]
    assert entry["is_success"] is True
    masses = entry["masses"]
    # single (layer, head) = (0, 0).
    assert set(masses.keys()) == {(0, 0)}
    comp_masses = masses[(0, 0)]
    # uniform 1/6 row → normalized mass = span_width / 6.
    assert comp_masses["benign_puzzle_scaffold"] == pytest.approx(4 / 6)
    assert comp_masses["harmful_instruction"] == pytest.approx(2 / 6)
    assert comp_masses["final_answer_cue"] == pytest.approx(2 / 6)
    assert comp_masses["injected_reasoning"] == pytest.approx(0.0)


# --------------------------------------------------------------------------- #
# discovery_test_split determinism
# --------------------------------------------------------------------------- #
def test_split_deterministic_and_partitions():
    recs = [_mk_record(f"task_{i}", True, 10, {}) for i in range(200)]
    d1, t1 = drv.discovery_test_split(recs)
    d2, t2 = drv.discovery_test_split(recs)
    # Deterministic: identical partition on repeat.
    ids_d1 = [r["task_id"] for r in d1]
    ids_d2 = [r["task_id"] for r in d2]
    assert ids_d1 == ids_d2
    # Disjoint + covering.
    assert len(d1) + len(t1) == 200
    assert set(ids_d1).isdisjoint({r["task_id"] for r in t1})
    # Roughly frac=0.5 (allow generous slack for 200 md5 draws).
    assert 60 <= len(d1) <= 140


def test_split_missing_task_id_goes_to_test():
    recs = [_mk_record(None, True, 10, {}, with_goal=False)]
    d, t = drv.discovery_test_split(recs)
    assert d == []
    assert len(t) == 1


# --------------------------------------------------------------------------- #
# run_probe end-to-end + hand-computed contrast
# --------------------------------------------------------------------------- #
def test_run_probe_writes_csv_and_contrast(tmp_path):
    # Force both records into DISCOVERY (frac=1.0) so the contrast is exact.
    succ = _record_with_cue()  # is_success True
    fail = _record_with_cue()
    fail["task_id"] = "task_C"
    fail["is_success"] = False
    path = _write_jsonl(tmp_path, [succ, fail])
    out_csv = os.path.join(str(tmp_path), "contrast.csv")

    result = drv.run_probe(
        path, fake_forward_fn, out_csv, top_k=5,
    )
    # Both records are pushed to discovery only if their hash lands there; make
    # the assertion robust by recomputing against whatever landed in discovery.
    contrast = result["contrast"]
    assert (0, 0) in contrast

    # Under the uniform fake forward every record yields identical masses, so for
    # any component succ_mean == fail_mean == width/6 and delta == 0 whenever both
    # outcomes are present; if only one outcome landed in discovery, the missing
    # side is 0.0. Recompute expected from the split.
    records = drv.load_records(path)
    disc, _ = drv.discovery_test_split(records)
    n_succ = sum(1 for r in disc if r["is_success"])
    n_fail = sum(1 for r in disc if not r["is_success"])

    cell = contrast[(0, 0)]["benign_puzzle_scaffold"]
    exp_succ = (4 / 6) if n_succ else 0.0
    exp_fail = (4 / 6) if n_fail else 0.0
    assert cell["succ_mean"] == pytest.approx(exp_succ)
    assert cell["fail_mean"] == pytest.approx(exp_fail)
    assert cell["delta"] == pytest.approx(exp_succ - exp_fail)
    assert cell["n_succ"] == n_succ
    assert cell["n_fail"] == n_fail

    # CSV written with the tidy schema.
    assert os.path.exists(out_csv)
    with open(out_csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows
    assert set(rows[0].keys()) == {
        "layer",
        "head",
        "component",
        "succ_mean",
        "fail_mean",
        "delta",
        "n_succ",
        "n_fail",
    }
    # top_heads keyed by every default component.
    assert set(result["top_heads"].keys()) == set(drv.DEFAULT_COMPONENTS)
    assert result["n_discovery"] + result["n_test"] == 2


def test_run_probe_exact_contrast_single_bucket(tmp_path):
    """Deterministically place ONE success and ONE failure in discovery.

    Pick task_ids whose md5 buckets are both < 50 so frac=0.5 keeps both, giving
    an exact hand-computed delta of 0 (uniform forward) with n_succ=n_fail=1.
    """
    import hashlib

    def bucket(tid):
        return int(hashlib.md5(tid.encode()).hexdigest()[:8], 16) % 100

    succ_id = next(f"s{i}" for i in range(1000) if bucket(f"s{i}") < 50)
    fail_id = next(f"f{i}" for i in range(1000) if bucket(f"f{i}") < 50)

    succ = _record_with_cue()
    succ["task_id"] = succ_id
    succ["is_success"] = True
    fail = _record_with_cue()
    fail["task_id"] = fail_id
    fail["is_success"] = False

    path = _write_jsonl(tmp_path, [succ, fail])
    out_csv = os.path.join(str(tmp_path), "contrast2.csv")
    result = drv.run_probe(path, fake_forward_fn, out_csv)

    assert result["n_discovery"] == 2
    cell = result["contrast"][(0, 0)]["final_answer_cue"]
    assert cell["n_succ"] == 1
    assert cell["n_fail"] == 1
    assert cell["succ_mean"] == pytest.approx(2 / 6)
    assert cell["fail_mean"] == pytest.approx(2 / 6)
    assert cell["delta"] == pytest.approx(0.0)


# --------------------------------------------------------------------------- #
# import is torch-free
# --------------------------------------------------------------------------- #
def _import_pulls_in_torch(*module_names):
    """Import ``module_names`` in a FRESH interpreter; return True iff that
    import pulled ``torch`` into the CHILD's ``sys.modules``.

    This probe must run out-of-process. pytest imports every collected test
    module before running any test, and several sibling test modules import
    torch at module scope, so an in-process ``"torch" in sys.modules`` check
    would assert a property of the SESSION rather than of the module under
    test. The child gets the repo root and ``scripts/`` on PYTHONPATH, exactly
    like the in-process import above. Any child failure that is not the
    torch question itself is raised loudly, so an ImportError can never be
    silently read as "torch-free".
    """
    import os
    import subprocess

    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _child = (
        "import importlib, sys\n"
        "for _name in sys.argv[1:]:\n"
        "    importlib.import_module(_name)\n"
        "print('TORCH' if 'torch' in sys.modules else 'NOTORCH')\n"
    )
    _env = dict(os.environ)
    _pp = [_root, os.path.join(_root, "scripts")]
    if _env.get("PYTHONPATH"):
        _pp.append(_env["PYTHONPATH"])
    _env["PYTHONPATH"] = os.pathsep.join(_pp)
    _proc = subprocess.run(
        [sys.executable, "-c", _child, *module_names],
        capture_output=True,
        text=True,
        env=_env,
    )
    _lines = _proc.stdout.strip().splitlines()
    _verdict = _lines[-1].strip() if _lines else ""
    if _proc.returncode != 0 or _verdict not in ("TORCH", "NOTORCH"):
        raise AssertionError(
            "torch-free probe subprocess failed for {!r} (returncode={})\n"
            "--- child stdout ---\n{}\n--- child stderr ---\n{}".format(
                list(module_names), _proc.returncode, _proc.stdout, _proc.stderr
            )
        )
    return _verdict == "TORCH"


def test_import_is_torch_free():
    assert not _import_pulls_in_torch("scripts.phase_f_probe_driver")


# --------------------------------------------------------------------------- #
# component_token_length
# --------------------------------------------------------------------------- #
def test_component_token_length_sums_instance_ranges():
    """Multiple located instances → sum of (tok_end - tok_start)."""
    spans = {
        "benign_puzzle_scaffold": {
            "located": True,
            "instances": [_mk_instance(0, 10, 0, 4), _mk_instance(20, 30, 10, 13)],
        },
    }
    rec = _mk_record("t", True, 20, spans)
    # (4-0) + (13-10) = 4 + 3 = 7.
    assert drv.component_token_length(rec, "benign_puzzle_scaffold") == 7


def test_component_token_length_unlocated_is_zero():
    rec = _record_with_cue()  # injected_reasoning is unlocated.
    assert drv.component_token_length(rec, "injected_reasoning") == 0
    # final_answer_cue covers [4,6) → 2 tokens; harmful_instruction [0,2) → 2.
    assert drv.component_token_length(rec, "final_answer_cue") == 2
    assert drv.component_token_length(rec, "harmful_instruction") == 2
    assert drv.component_token_length(rec, "benign_puzzle_scaffold") == 4


# --------------------------------------------------------------------------- #
# build_per_record_meta — parallel path carrying confound metadata
# --------------------------------------------------------------------------- #
def two_head_forward_fn(record):
    """[n_layers=1, n_heads=2, n_q=6, n_k=6].

    head 0: uniform 1/6 over keys → mass into a width-w span = w/6.
    head 1: every row = [1,0,0,0,0,0] → all mass on key 0.
    """
    attn = np.zeros((1, 2, 6, 6), dtype=np.float64)
    attn[0, 0, :, :] = 1.0 / 6.0
    attn[0, 1, :, 0] = 1.0
    return attn


def test_build_per_record_meta_carries_n_tokens_and_comp_lens():
    recs = [_record_with_cue()]
    meta = drv.build_per_record_meta(recs, fake_forward_fn)
    assert len(meta) == 1
    entry = meta[0]
    assert entry["is_success"] is True
    assert entry["n_tokens"] == 6
    assert set(entry.keys()) == {"is_success", "n_tokens", "masses", "comp_lens"}
    assert entry["comp_lens"] == {
        "benign_puzzle_scaffold": 4,
        "harmful_instruction": 2,
        "final_answer_cue": 2,
        "injected_reasoning": 0,
    }
    # masses match build_per_record exactly (parallel path, same computation).
    assert entry["masses"] == drv.build_per_record(recs, fake_forward_fn)[0]["masses"]


def test_build_per_record_meta_skips_none_forward():
    recs = [_record_with_cue(), _record_no_cue()]

    def ff(record):
        return None if record["task_id"] == "task_A" else fake_forward_fn(record)

    meta = drv.build_per_record_meta(recs, ff)
    assert len(meta) == 1
    assert meta[0]["is_success"] is False  # task_B kept


# --------------------------------------------------------------------------- #
# write_per_record_csv — long-format shape, mean-over-heads, anonymity
# --------------------------------------------------------------------------- #
def test_write_per_record_csv_shape_and_mean_over_heads(tmp_path):
    succ = _record_with_cue()
    fail = _record_with_cue()
    fail["task_id"] = "task_C"
    fail["is_success"] = False
    recs = [succ, fail]

    meta = drv.build_per_record_meta(recs, two_head_forward_fn)
    out_csv = os.path.join(str(tmp_path), "per_record.csv")
    drv.write_per_record_csv(meta, list(drv.DEFAULT_COMPONENTS), out_csv)

    with open(out_csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # n_records(2) × n_layers(1) × n_components(4) = 8 rows.
    assert len(rows) == 2 * 1 * len(drv.DEFAULT_COMPONENTS)
    assert set(rows[0].keys()) == {
        "record_index",
        "is_success",
        "n_tokens",
        "component",
        "layer",
        "mean_mass_over_heads",
        "component_tok_len",
    }

    # record_index is anonymous 0..N-1 (never task_id).
    assert sorted({int(r["record_index"]) for r in rows}) == [0, 1]

    # Mean over heads: head0 = w/6, head1 = 1.0 for keys touching 0 else 0.
    # scaffold [0,4): head0=4/6, head1=1.0 → mean=(4/6+1)/2.
    # final_answer_cue [4,6): head0=2/6, head1=0 → mean=(2/6)/2 = 1/6.
    by = {(int(r["record_index"]), r["component"]): r for r in rows}
    scaf = by[(0, "benign_puzzle_scaffold")]
    assert float(scaf["mean_mass_over_heads"]) == pytest.approx((4 / 6 + 1.0) / 2)
    assert int(scaf["component_tok_len"]) == 4
    assert int(scaf["n_tokens"]) == 6
    cue = by[(0, "final_answer_cue")]
    assert float(cue["mean_mass_over_heads"]) == pytest.approx((2 / 6) / 2)
    assert int(cue["component_tok_len"]) == 2
    # is_success recorded per record.
    assert by[(0, "benign_puzzle_scaffold")]["is_success"] == "True"
    assert by[(1, "benign_puzzle_scaffold")]["is_success"] == "False"


def test_per_record_csv_is_anonymous_no_text_leak(tmp_path):
    """The per-record CSV must never carry task_id/goal/preview sentinels."""
    succ = _record_with_cue()  # task_A + decoy goal/preview
    fail = _record_with_cue()
    fail["task_id"] = "task_C"
    fail["is_success"] = False
    path = _write_jsonl(tmp_path, [succ, fail])
    out_csv = os.path.join(str(tmp_path), "contrast.csv")
    pr_csv = os.path.join(str(tmp_path), "per_record.csv")

    drv.run_probe(path, fake_forward_fn, out_csv, per_record_csv=pr_csv)

    assert os.path.exists(pr_csv)
    with open(pr_csv, "r", encoding="utf-8") as f:
        blob = f.read()
    assert _DECOY_GOAL not in blob
    assert _DECOY_PREVIEW not in blob
    assert "task_A" not in blob
    assert "task_C" not in blob
    assert "task_id" not in blob


def test_run_probe_default_no_per_record_csv_unchanged(tmp_path):
    """Default run_probe (no per_record_csv) writes no extra file and returns same shape."""
    succ = _record_with_cue()
    fail = _record_with_cue()
    fail["task_id"] = "task_C"
    fail["is_success"] = False
    path = _write_jsonl(tmp_path, [succ, fail])
    out_csv = os.path.join(str(tmp_path), "contrast.csv")

    result = drv.run_probe(path, fake_forward_fn, out_csv)
    assert set(result.keys()) == {"contrast", "top_heads", "n_discovery", "n_test"}
    # No stray per-record CSV created in the tmp dir.
    extra = [
        n for n in os.listdir(str(tmp_path))
        if n.endswith(".csv") and n != "contrast.csv"
    ]
    assert extra == []


def test_build_per_record_skips_none_forward(tmp_path):
    """A forward_fn returning None (recoverable per-record failure) is dropped, not fatal."""
    import numpy as np
    recs = [
        {"is_success": True, "n_tokens": 6, "task_id": "a",
         "spans": {"final_answer_cue": {"located": True, "instances": [{"tok_start": 4, "tok_end": 6}]}}},
        {"is_success": False, "n_tokens": 6, "task_id": "b",
         "spans": {"final_answer_cue": {"located": True, "instances": [{"tok_start": 4, "tok_end": 6}]}}},
    ]
    def ff(record):
        return None if record["task_id"] == "a" else np.ones((1, 1, 6, 6)) / 6.0
    out = drv.build_per_record(recs, ff, components=["final_answer_cue"])
    assert len(out) == 1  # 'a' skipped, 'b' kept
    assert out[0]["is_success"] is False
