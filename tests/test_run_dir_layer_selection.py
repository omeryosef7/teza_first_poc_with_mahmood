"""S-104: a tag that resolves to TWO complete run dirs must be separated by a RECORDED property.

The defect these lock down. Until S-103 every run tag had exactly one complete directory, so
"complete" and "unique" were the same predicate and nothing had to distinguish them. S-103 re-ran
the same eighteen button-TRAIN arms at layer 18 under the SAME tags as their layer-20 originals.
Every one of those tags now resolves to two complete directories that differ only in which layer
they patched -- two different experiments wearing one name.

Both analysis paths already refused that ambiguity, which was right but is not an analysis. The
fix must narrow the set by something the run itself recorded (config.json's rescue_layer,
RUNMETA.json's slurm_job_id) and must NEVER tie-break on recency. These tests assert BOTH halves,
because a selector that silently picks one is worse than the refusal it replaced:

  * the filter SELECTS the requested layer out of an ambiguous pair, and
  * the filter still REFUSES when it cannot separate them, and
  * a single dir of the WRONG layer is refused rather than accepted by default, which is the case
    an "if more than one" guard would skip entirely.
"""
import importlib.util
import json
import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, relpath))
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def _mkrun(root, tag, stamp, n_rows, rescue_layer, job, status="ok"):
    """A minimal but STRUCTURALLY REAL run dir: the files the selectors actually read."""
    d = os.path.join(root, "%s_%s_1" % (tag, stamp))
    os.makedirs(d)
    with open(os.path.join(d, "results.jsonl"), "w") as fh:
        for i in range(n_rows):
            fh.write(json.dumps({"prompt_id": "p%d" % i, "rescue_layer": rescue_layer}) + "\n")
    with open(os.path.join(d, "gens.jsonl"), "w") as fh:
        for i in range(n_rows):
            fh.write(json.dumps({"prompt_id": "p%d" % i, "domain": "d", "generation": ""}) + "\n")
    json.dump({"schema": "DONE/1", "status": status, "rows_written": n_rows},
              open(os.path.join(d, "DONE.json"), "w"))
    json.dump({"args": {"rescue_layer": rescue_layer, "arm": tag.split("_")[-1]}},
              open(os.path.join(d, "config.json"), "w"))
    json.dump({"slurm_job_id": job, "hostname": "n-999"},
              open(os.path.join(d, "RUNMETA.json"), "w"))
    return d


@pytest.fixture()
def paths(tmp_path, monkeypatch):
    """Both paths resolve against a module-level directory; point both at a scratch one."""
    primary = _load("rederive_patch_s104", "scripts/dcs_csi_rederive_patch.py")
    indep = _load("rederive_subspace_s104", "scripts/dcs_csi_rederive_subspace.py")
    monkeypatch.setattr(primary, "SCORE_DIR", str(tmp_path))
    monkeypatch.setattr(indep, "SB", str(tmp_path))
    return primary, indep, str(tmp_path)


def test_ambiguous_pair_is_separated_by_the_layer_it_recorded(paths):
    """THE regression: two complete dirs, one per layer -> the requested layer is returned."""
    primary, indep, root = paths
    l20 = _mkrun(root, "t_KO_AXIS", "20260915_195425", 670, 20, "896679")
    l18 = _mkrun(root, "t_KO_AXIS", "20260917_011438", 670, 18, "902004")

    assert primary.strict_run_dir("t_KO_AXIS", 670, row_file="results.jsonl",
                                  require_rescue_layer=18) == l18
    assert primary.strict_run_dir("t_KO_AXIS", 670, row_file="results.jsonl",
                                  require_rescue_layer=20) == l20
    assert indep.run_dir("t_KO_AXIS", 670, 0, layer=18) == l18
    assert indep.run_dir("t_KO_AXIS", 670, 0, layer=20) == l20


def test_it_still_refuses_when_nothing_separates_them(paths):
    """The no-rescue arms (BASE, KO) carry no layer: the layer filter must NOT invent a winner."""
    primary, indep, root = paths
    _mkrun(root, "t_BASE", "20260915_190347", 670, None, "896679")
    _mkrun(root, "t_BASE", "20260917_001351", 670, None, "902004")

    with pytest.raises(SystemExit) as e:
        primary.strict_run_dir("t_BASE", 670, row_file="results.jsonl", require_rescue_layer=18)
    assert "need exactly 1" in str(e.value)
    with pytest.raises(SystemExit):
        indep.run_dir("t_BASE", 670, 0, layer=18)


def test_the_slurm_job_separates_the_arms_that_have_no_layer(paths):
    """...and the allocation, which every run records, is what does separate them."""
    primary, indep, root = paths
    _mkrun(root, "t_BASE", "20260915_190347", 670, None, "896679")
    new = _mkrun(root, "t_BASE", "20260917_001351", 670, None, "902004")

    assert primary.strict_run_dir("t_BASE", 670, row_file="results.jsonl",
                                  require_slurm_jobs=["902004", "902005"]) == new
    assert indep.run_dir("t_BASE", 670, 0, jobs=["902004", "902005"]) == new


def test_a_lone_dir_of_the_WRONG_layer_is_refused_not_accepted(paths):
    """The case a 'disambiguate only when >1' guard skips: one dir, and it is the wrong experiment.

    Without this assertion, asking for L18 in a directory that only holds the L20 run would return
    the L20 run and every downstream number would be labelled L18. That is the failure mode the
    whole change exists to prevent, and it is NOT covered by the ambiguity tests above.
    """
    primary, indep, root = paths
    _mkrun(root, "t_KO_AXIS", "20260915_195425", 670, 20, "896679")

    with pytest.raises(SystemExit) as e:
        primary.strict_run_dir("t_KO_AXIS", 670, row_file="results.jsonl", require_rescue_layer=18)
    assert "not the required 18" in str(e.value)
    with pytest.raises(SystemExit):
        indep.run_dir("t_KO_AXIS", 670, 0, layer=18)


def test_selection_is_never_a_tie_break_on_time(paths):
    """Three complete dirs, two of them the requested layer -> refuse. Never 'the newest one'."""
    primary, indep, root = paths
    _mkrun(root, "t_KO_AXIS", "20260915_195425", 670, 20, "896679")
    _mkrun(root, "t_KO_AXIS", "20260917_011438", 670, 18, "902004")
    _mkrun(root, "t_KO_AXIS", "20260918_011438", 670, 18, "902999")

    with pytest.raises(SystemExit):
        primary.strict_run_dir("t_KO_AXIS", 670, row_file="results.jsonl", require_rescue_layer=18)
    with pytest.raises(SystemExit):
        indep.run_dir("t_KO_AXIS", 670, 0, layer=18)


def test_unfiltered_behaviour_is_unchanged(paths):
    """The 164 results already in the record were produced with no filter; that path must not move."""
    primary, indep, root = paths
    only = _mkrun(root, "t_KO", "20260915_191231", 670, None, "896679")
    assert primary.strict_run_dir("t_KO", 670, row_file="results.jsonl") == only
    assert indep.run_dir("t_KO", 670, 0) == only
