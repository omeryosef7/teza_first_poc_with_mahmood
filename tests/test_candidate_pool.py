"""Unit tests for the candidate-pool CAPTURE + RERANK core (Package-1 Condition 3).

PURE-PYTHON / CPU-only: no torch, no model, no GPU. Runs under:
    /usr/bin/python3 -m pytest tests/test_candidate_pool.py -v

Proves on toy pools (per the task spec):
  - capture schema round-trips (write -> read -> same fields);
  - selection picks the max-BEHAVIORAL-REWARD candidate;
  - ties are deterministic (reward tie -> lower proxy_loss -> lexicographic);
  - empty pool / empty candidate list handled without crashing;
  - top-K truncation + rank ordering are correct.
"""

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from reinforce_objective import candidate_pool as CP  # noqa: E402
from reinforce_objective import rerank_runner as RR  # noqa: E402


# ---------------------------------------------------------------------------
# select_top_k / capture_pool_records
# ---------------------------------------------------------------------------

def test_select_top_k_orders_by_loss_and_truncates():
    strs = ["a", "b", "c", "d"]
    losses = [0.9, 0.1, 0.5, 0.3]
    top = CP.select_top_k(strs, losses, top_k=2)
    assert [t[1] for t in top] == ["b", "d"]          # lowest two losses
    assert [t[2] for t in top] == [0.1, 0.3]


def test_select_top_k_tie_is_deterministic_by_orig_index():
    strs = ["x", "y", "z"]
    losses = [0.5, 0.5, 0.5]                            # all tied
    top = CP.select_top_k(strs, losses, top_k=None)
    assert [t[0] for t in top] == [0, 1, 2]            # original index order
    assert [t[1] for t in top] == ["x", "y", "z"]


def test_select_top_k_length_mismatch_raises():
    with pytest.raises(ValueError):
        CP.select_top_k(["a", "b"], [0.1])


def test_capture_records_have_full_schema_and_ranks():
    recs = CP.capture_pool_records(
        step=3,
        candidate_strs=["a", "b", "c"],
        proxy_losses=[0.2, 0.1, 0.3],
        top_k=2,
        candidate_ids=[[1, 2], [3, 4], [5, 6]],
    )
    assert len(recs) == 2
    for rank, rec in enumerate(recs):
        assert set(rec) == {
            CP.F_STEP, CP.F_RANK, CP.F_TRIGGER_STR,
            CP.F_PROXY_LOSS, CP.F_TRIGGER_IDS, CP.F_N_POOL,
        }
        assert rec[CP.F_STEP] == 3
        assert rec[CP.F_RANK] == rank
        assert rec[CP.F_N_POOL] == 3                    # before truncation
    assert recs[0][CP.F_TRIGGER_STR] == "b"             # lowest loss first
    assert recs[0][CP.F_TRIGGER_IDS] == [3, 4]


# ---------------------------------------------------------------------------
# writer round-trip
# ---------------------------------------------------------------------------

def test_writer_roundtrip_preserves_records(tmp_path):
    path = tmp_path / "pool.jsonl"
    with CP.CandidatePoolWriter(path, top_k=2) as w:
        n0 = w.write_step(0, ["a", "b", "c"], [0.3, 0.1, 0.2], [[1], [2], [3]])
        n1 = w.write_step(1, ["d", "e"], [0.9, 0.4], [[4], [5]])
    assert (n0, n1) == (2, 2)

    recs = CP.read_pool(path)
    assert len(recs) == 4

    groups = CP.group_by_step(recs)
    assert set(groups) == {0, 1}
    # step 0 top-2 by loss: b(0.1), c(0.2)
    assert [r[CP.F_TRIGGER_STR] for r in groups[0]] == ["b", "c"]
    # step 1 top-2 by loss: e(0.4), d(0.9)
    assert [r[CP.F_TRIGGER_STR] for r in groups[1]] == ["e", "d"]
    # exact float + ids survive the JSON round-trip
    assert groups[0][0][CP.F_PROXY_LOSS] == 0.1
    assert groups[0][0][CP.F_TRIGGER_IDS] == [2]


def test_writer_top_k_none_keeps_all(tmp_path):
    path = tmp_path / "pool.jsonl"
    with CP.CandidatePoolWriter(path) as w:
        w.write_step(0, ["a", "b", "c"], [0.3, 0.1, 0.2])
    assert len(CP.read_pool(path)) == 3


# ---------------------------------------------------------------------------
# rerank: parse / dedupe
# ---------------------------------------------------------------------------

def test_parse_pool_dedupes_keeping_best_loss(tmp_path):
    path = tmp_path / "pool.jsonl"
    with CP.CandidatePoolWriter(path) as w:
        w.write_step(0, ["dup", "solo"], [0.5, 0.7])
        w.write_step(1, ["dup"], [0.2])                 # same str, better loss, later step
    cands = RR.parse_pool(path)
    assert len(cands) == 2                              # "dup" collapsed to one
    dup = next(c for c in cands if c.trigger_str == "dup")
    assert dup.proxy_loss == 0.2                        # best (lowest) kept
    assert dup.first_step == 0                          # earliest step kept
    assert dup.count == 2
    # sorted best-first by proxy_loss
    assert cands[0].trigger_str == "dup"


def test_parse_pool_max_candidates_caps_after_sort(tmp_path):
    path = tmp_path / "pool.jsonl"
    with CP.CandidatePoolWriter(path) as w:
        w.write_step(0, ["a", "b", "c"], [0.9, 0.1, 0.5])
    cands = RR.parse_pool(path, max_candidates=2)
    assert [c.trigger_str for c in cands] == ["b", "c"]


# ---------------------------------------------------------------------------
# rerank: selection by behavioral reward
# ---------------------------------------------------------------------------

def _cand(s, loss):
    return RR.RerankCandidate(trigger_str=s, proxy_loss=loss, first_step=0, count=1)


def test_selection_picks_max_reward_not_min_loss():
    # Lowest proxy_loss ("a") is NOT the highest behavioral reward -> reward wins.
    cands = [_cand("a", 0.1), _cand("b", 0.5), _cand("c", 0.9)]
    rewards = [0.2, 0.8, 0.3]
    res = RR.select_by_precomputed_rewards(cands, rewards)
    assert res.best_trigger_str == "b"
    assert res.best_reward == 0.8
    assert res.n_candidates_scored == 3
    assert res.ranking[0]["trigger_str"] == "b"        # best-first ordering


def test_selection_reward_tie_broken_by_lower_proxy_loss():
    cands = [_cand("hi", 0.8), _cand("lo", 0.2)]
    rewards = [0.5, 0.5]                                # tie
    res = RR.select_by_precomputed_rewards(cands, rewards)
    assert res.best_trigger_str == "lo"                # lower proxy_loss wins


def test_selection_full_tie_broken_lexicographically():
    cands = [_cand("zzz", 0.4), _cand("aaa", 0.4)]
    rewards = [0.7, 0.7]                                # reward + loss tie
    res = RR.select_by_precomputed_rewards(cands, rewards)
    assert res.best_trigger_str == "aaa"               # lexicographic tie-break


def test_selection_empty_is_null_result():
    res = RR.select_by_precomputed_rewards([], [])
    assert res.best_trigger_str is None
    assert res.n_candidates_scored == 0
    assert res.ranking == []


def test_selection_length_mismatch_raises():
    with pytest.raises(ValueError):
        RR.select_by_precomputed_rewards([_cand("a", 0.1)], [0.5, 0.6])


def test_parse_empty_pool_file(tmp_path):
    path = tmp_path / "empty.jsonl"
    path.write_text("")
    assert RR.parse_pool(path) == []


# ---------------------------------------------------------------------------
# rerank_pool end-to-end with injected (mock) generate + reward (still no torch)
# ---------------------------------------------------------------------------

def test_rerank_pool_with_injected_callables(tmp_path):
    path = tmp_path / "pool.jsonl"
    with CP.CandidatePoolWriter(path) as w:
        w.write_step(0, ["good", "bad", "meh"], [0.3, 0.1, 0.2])

    # mock free-generation: response is just a tag of the trigger
    def generate_fn(trigger):
        return {"good": "here is how step 1", "bad": "I cannot help",
                "meh": "maybe"}[trigger]

    # mock behavioral reward: harmful-looking response scores high
    def reward_fn(goal, response):
        assert goal == "how to X"                       # goal is threaded through
        return 1.0 if "step 1" in response else 0.0

    res = RR.rerank_pool(path, goal="how to X",
                         reward_fn=reward_fn, generate_fn=generate_fn,
                         max_candidates=16)
    # "bad" has the lowest proxy_loss but "good" wins on behavioral reward.
    assert res.best_trigger_str == "good"
    assert res.best_reward == 1.0


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


def test_module_imports_without_torch():
    assert not _import_pulls_in_torch(
        "reinforce_objective.candidate_pool", "reinforce_objective.rerank_runner"
    )


def test_probe_detects_a_module_that_does_import_torch():
    """Negative control: the probe must be able to say YES.

    Without this, a helper that always returned False would make every
    torch-free assertion in this repo vacuously green.
    """
    assert _import_pulls_in_torch("torch")
