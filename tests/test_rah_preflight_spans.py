"""RAH-C-005: the token-span resolver must use OVERLAP, not containment.

A BPE tokenizer emits the leading space as part of the word token, so a word at [870,876) is
carried by a token spanning [869,876). A containment test finds nothing. This file pins the rule
and proves the guard can still fail.
"""
import os
import sys

import types

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "src", "boombness"))
import rah_preflight_transport as pf  # noqa: E402


def test_leading_space_token_is_resolved():
    """The real failing case: ' poison' spans [869,876) for a word at [870,876)."""
    offsets = [(860, 869), (869, 876), (876, 877)]
    assert pf.token_index_covering(offsets, 870, 876) == 1


def test_MUTANT_containment_semantics_would_have_failed():
    """Executed proof that the OLD rule was broken on the same input."""
    offsets = [(860, 869), (869, 876), (876, 877)]
    old_hits = [k for k, (a, b) in enumerate(offsets) if a >= 870 and b <= 876 and b > a]
    assert old_hits == [], "the old containment rule should find nothing here"


def test_multi_subtoken_word_returns_the_LAST_piece():
    offsets = [(860, 869), (869, 872), (872, 876), (876, 877)]
    assert pf.token_index_covering(offsets, 870, 876) == 2


def test_no_overlap_still_raises():
    with pytest.raises(ValueError):
        pf.token_index_covering([(0, 5), (5, 10)], 20, 26)


def test_zero_width_tokens_are_ignored():
    offsets = [(869, 869), (869, 876)]
    assert pf.token_index_covering(offsets, 870, 876) == 1


class _Tok:
    def __init__(self, m): self.m = m
    def decode(self, ids): return self.m[ids[0]]


def test_assert_token_is_part_of_accepts_a_real_piece():
    assert pf.assert_token_is_part_of(_Tok({7: " poison"}), [7], 0, "poison", "x") == "poison"


def test_MUTANT_assert_token_is_part_of_REJECTS_a_wrong_token():
    with pytest.raises(SystemExit):
        pf.assert_token_is_part_of(_Tok({7: " lantern"}), [7], 0, "poison", "x")


def test_pr002_fewshot_forms_name_no_candidate_and_are_two_hop():
    """`RAH2-PR-002`: the few-shot forms must constrain the slot WITHOUT printing a candidate.

    Text-level, so it needs no tokenizer. The geometry half (patch at the probe, read 2 tokens
    later at ` ->`) is asserted through `patch_at`/`read_at` rather than by tokenizing.
    """
    labels = ["poison", "lantern", "missile", "candle"]
    forms = pf.fewshot_receiver_forms(*labels, "widget")
    by = {f["name"]: f for f in forms}
    assert set(by) == {"id07_raw", "id07_tmpl", "fc_probe_last", "fewshot_cat", "fewshot_syn"}
    # `RAH2-PR-003`: the untemplated echo control must be present, or a mass difference between
    # the few-shot forms and the references cannot be attributed to framing rather than template.
    assert by["id07_raw"]["templated"] is False
    assert all(by[n]["templated"] is False for n in ("fewshot_cat", "fewshot_syn"))
    for name in ("fewshot_cat", "fewshot_syn"):
        f = by[name]
        assert pf.names_any_candidate(f["body"], labels) == [], name
        assert (f["patch_at"], f["read_at"], f["templated"]) == ("probe", "final", False), name
        assert f["body"].endswith('"widget" ->'), name
        assert f["body"].count("\n") == 3, name        # three demonstrated pairs, then the probe
    # the reference extremes are carried through UNCHANGED from the frozen grid
    grid = {f["name"]: f for f in pf.receiver_forms(*labels, "widget")}
    for name in ("id07_raw", "id07_tmpl", "fc_probe_last"):
        assert by[name] == grid[name], name


def test_pr002_exemplars_are_disjoint_from_the_candidate_vocabularies():
    """No exemplar may BE a candidate. (First-token collision needs a tokenizer and is checked in
    the run itself by `exemplar_candidate_collisions`; this is the text-level floor.)"""
    for labels in (["poison", "lantern", "missile", "candle"],
                   ["bomb", "carrot", "knife", "ticket"]):
        assert not (set(pf.EXEMPLAR_WORDS) & set(labels))


def test_d11_provenance_block_is_emitted_and_complete():
    """`RAH2-DR-002` D11: provenance must be ATTESTED in the artifact, not asserted in prose.

    Every job id and commit in the RAH2 log is prose, checkable only against SLURM logs that are not
    part of the record. This asserts the block exists, carries the fields a reader needs, and is
    actually wired into the written dict.

    ⚠ The wiring half is a source check, not a round-trip: running `main()` needs a GPU and a model
    load. It catches the key being dropped from `out`, not a bug in what it holds.
    """
    p = pf.provenance()
    for k in ("git_commit", "git_dirty", "slurm_job_id", "slurm_nodelist", "hostname", "argv",
              "started_utc", "finished_utc", "python"):
        assert k in p, k
    assert isinstance(p["git_dirty"], bool)          # never a string -- it is read as a condition
    assert isinstance(p["argv"], list)
    assert p["git_commit"] is None or len(p["git_commit"]) == 40
    src = open(pf.__file__, encoding="utf-8").read()
    assert '"provenance": prov' in src, "provenance() exists but is not written into the artifact"
    # `RAH2-C-030` F4: the written object must come FROM the function. Without this, replacing
    # `prov = provenance()` with `prov = {}` shipped a 2-field block and the guard stayed green.
    assert "prov = provenance()" in src, "the written block is not provenance()'s return value"
    # `RAH2-C-030` F3: the old assertion only checked the stamp EXISTED. Moving the assignment to
    # after the model load left it green while making the log's sentence false. Positions, not
    # presence -- and the repo state must be sampled BEFORE the sweep, or it attests the wrong
    # commit (F2).
    i_stamp = src.index("started_utc = time.strftime")
    i_prov = src.index("prov = provenance()")
    i_load = src.index("dc.load_model(")
    i_sweep = src.index("for form in forms:")
    assert i_stamp < i_load, "started_utc is stamped AFTER the model load"
    assert i_prov < i_sweep, "provenance() is sampled AFTER the sweep -- it will attest the wrong commit"


def test_c030_git_dirty_is_tristate_and_never_claims_clean_on_failure():
    """`RAH2-C-030` F1. `git_dirty` False must mean *measured clean*, never *could not measure*.

    The first version collapsed both to False, so an artifact produced on a node without git would
    assert the code was unmodified. This pins the tri-state at the source, because a functional test
    would need git to be genuinely broken.
    """
    p = pf.provenance()
    assert p["git_dirty"] in (True, False, None)
    assert isinstance(p["git_ok"], bool)

    # FUNCTIONAL, not a source grep. `RAH2-C-030`: the first attempt at this guard asserted a
    # literal substring was absent, and a rewrite of the SAME defect
    # (`(bool(status) if ok_status else None)` -> `bool(status)`) sailed past it. Drive a failing
    # git instead and demand the tri-state.
    class _Boom:
        def __call__(self, *a, **k):
            raise OSError("git not found on this node")

    dead = pf.provenance(_run=_Boom())
    assert dead["git_ok"] is False
    assert dead["git_commit"] is None
    assert dead["git_dirty"] is None, (
        "git_dirty is %r when git cannot run -- an artifact would assert the code was unmodified "
        "by a run that could not read the repo at all" % (dead["git_dirty"],))

    class _NonZero:
        def __call__(self, *a, **k):
            return types.SimpleNamespace(returncode=128, stdout="", stderr="dubious ownership")

    refused = pf.provenance(_run=_NonZero())
    assert refused["git_ok"] is False and refused["git_dirty"] is None
