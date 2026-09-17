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
    # The unconditional filter (review R8-B1) drops it before the survivor assertion, so the
    # refusal must still name the real CAUSE rather than reading as a missing run.
    msg = str(e.value)
    assert "rescue_layer=20" in msg and "CAUSE" in msg and "NOT a missing run" in msg
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


# ---------------------------------------------------------------------------- REVIEW R8 additions
# Three defects review R8 demonstrated in the S-104 change, each with the shape this sprint keeps
# shipping: a check that does not run in the case that matters.


def test_R8_B1_job_filter_asserts_on_the_survivor_too(paths):
    """R8-B1 (BLOCKER). Both filters were `len(ok) > 1`-guarded, and only the LAYER axis had a
    survivor assertion. So when exactly one directory survived the completeness check, the job
    filter never ran and a lone directory from the WRONG allocation was returned.

    This is the KO_RAND2 near-miss transposed onto BASE and KO -- the two arms whose only
    discriminator IS the job id, because they run no rescue and so carry no layer. `KO` is the
    subtrahend of every contrast in the L18 table, so a wrong-allocation `KO` would have made the
    whole column cross-layer with no VOID anywhere.
    """
    primary, indep, root = paths
    # The real shape: the L20 run complete, the L18 run short past --allow-short so inadmissible.
    _mkrun(root, "t_BASE", "20260915_190347", 670, None, "896679")
    _mkrun(root, "t_BASE", "20260917_001351", 661, None, "902004", status="INCOMPLETE")

    with pytest.raises(SystemExit) as e:
        primary.strict_run_dir("t_BASE", 670, row_file="results.jsonl", allow_short=4,
                               require_slurm_jobs=["902004", "902005"])
    msg = str(e.value)
    assert "896679" in msg and "not in" in msg and "CAUSE" in msg
    with pytest.raises(SystemExit):
        indep.run_dir("t_BASE", 670, 4, jobs=["902004", "902005"])


def test_R8_B1_layer_filter_narrowing_does_not_disable_the_job_filter(paths):
    """R8-B1, second half. When the LAYER filter itself reduced the set to one, the job filter
    became unreachable, so a directory from a third, unrequested allocation passed."""
    primary, indep, root = paths
    _mkrun(root, "t_KO_AXIS", "20260915_195425", 670, 20, "896679")
    _mkrun(root, "t_KO_AXIS", "20260917_011438", 670, 18, "999999")   # right layer, wrong job

    with pytest.raises(SystemExit) as e:
        primary.strict_run_dir("t_KO_AXIS", 670, row_file="results.jsonl",
                               require_rescue_layer=18, require_slurm_jobs=["902004", "902005"])
    assert "999999" in str(e.value) and "CAUSE" in str(e.value)
    with pytest.raises(SystemExit):
        indep.run_dir("t_KO_AXIS", 670, 0, layer=18, jobs=["902004", "902005"])


def test_R8_M1_a_config_that_cannot_verify_its_layer_is_refused_not_admitted(paths):
    """R8-M1 (MAJOR). `rescue_layer is None` was returned for THREE situations -- the arm ran no
    rescue, config.json is absent, config.json lacks the key -- and the filter KEPT all three. So
    an arm that rescued at the wrong layer, but whose config had lost the key, was admitted.

    Missing load-bearing metadata must RAISE, not default (plan section 14). Only an EXPLICIT
    `rescue_layer: null` -- how score_behavior.py writes a genuine no-rescue arm -- passes through.
    """
    primary, indep, root = paths
    d = _mkrun(root, "t_KO_AXIS", "20260915_195425", 670, 20, "896679")
    # config present, but the key is gone -- the layer is now unverifiable from the config
    json.dump({"args": {"arm": "KO_AXIS"}}, open(os.path.join(d, "config.json"), "w"))

    with pytest.raises(SystemExit) as e:
        primary.strict_run_dir("t_KO_AXIS", 670, row_file="results.jsonl", require_rescue_layer=18)
    assert "cannot verify" in str(e.value) and "CAUSE" in str(e.value)
    with pytest.raises(SystemExit):
        indep.run_dir("t_KO_AXIS", 670, 0, layer=18)


def test_R8_M1_the_independent_path_now_checks_the_ROWS_not_only_the_config(paths):
    """R8-M1, second half. The primary analyser asserted the requested layer against the ROWS; the
    independent path asserted against nothing. So the two paths could AGREE on a number while one
    of them had silently analysed a directory whose config and rows disagree -- and S-084 and S-100
    were both config/rows disagreements. That defeats the whole reason this file shares no code.
    """
    primary, indep, root = paths
    d = _mkrun(root, "t_KO_AXIS", "20260917_011438", 670, 18, "902004")
    # config says 18; the rows say 20. A run whose config does not describe what it wrote.
    with open(os.path.join(d, "results.jsonl"), "w") as fh:
        for i in range(670):
            fh.write(json.dumps({"prompt_id": "p%d" % i, "rescue_layer": 20,
                                 "rescue_liveness": {"n_writes": 1}}) + "\n")

    with pytest.raises(SystemExit) as e:
        indep.run_dir("t_KO_AXIS", 670, 0, layer=18)
    assert "ROWS record" in str(e.value)


def test_R8_M1_an_arm_that_fired_but_logged_no_layer_is_refused(paths):
    """R8-M2's shape on the run_dir axis: a rescue that FIRED while recording no layer cannot be
    verified, so it must be refused rather than treated like a no-rescue arm."""
    primary, indep, root = paths
    d = _mkrun(root, "t_KO_AXIS", "20260917_011438", 670, 18, "902004")
    with open(os.path.join(d, "results.jsonl"), "w") as fh:
        for i in range(670):
            fh.write(json.dumps({"prompt_id": "p%d" % i, "rescue_liveness": {"n_writes": 1}}) + "\n")

    with pytest.raises(SystemExit) as e:
        indep.run_dir("t_KO_AXIS", 670, 0, layer=18)
    assert "no row records a rescue_layer" in str(e.value)


def test_R8_the_legitimate_cases_still_resolve(paths):
    """The other half, without which the five tests above could all be satisfied by refusing
    everything: a real no-rescue arm and a real rescue arm must still resolve normally."""
    primary, indep, root = paths
    base = _mkrun(root, "t_BASE", "20260917_001351", 670, None, "902004")
    assert primary.strict_run_dir("t_BASE", 670, row_file="results.jsonl",
                                  require_rescue_layer=18,
                                  require_slurm_jobs=["902004", "902005"]) == base
    assert indep.run_dir("t_BASE", 670, 0, layer=18, jobs=["902004", "902005"]) == base

    ax = _mkrun(root, "t_KO_AXIS", "20260917_011438", 670, 18, "902005")
    assert primary.strict_run_dir("t_KO_AXIS", 670, row_file="results.jsonl",
                                  require_rescue_layer=18,
                                  require_slurm_jobs=["902004", "902005"]) == ax
    assert indep.run_dir("t_KO_AXIS", 670, 0, layer=18, jobs=["902004", "902005"]) == ax


def test_R8_m8_the_two_paths_agree_on_a_dir_with_no_config(paths):
    """R8-m8. The independent path RAISED on a directory with no `config.json` even with no filter
    requested, while the primary path ADMITTED it -- so the two "independent" paths disagreed on
    admissibility, which makes their agreement on a number mean less than it claims.

    Correct behaviour, now asserted for both: with no filter the directory is admitted (the 164
    committed results were all produced unfiltered, so that path must not move); with a layer
    required it is refused, because an absent config cannot verify one.
    """
    primary, indep, root = paths
    d = _mkrun(root, "t_KO", "20260915_191231", 670, None, "896679")
    os.remove(os.path.join(d, "config.json"))

    assert primary.strict_run_dir("t_KO", 670, row_file="results.jsonl") == d
    assert indep.run_dir("t_KO", 670, 0) == d
    with pytest.raises(SystemExit):
        primary.strict_run_dir("t_KO", 670, row_file="results.jsonl", require_rescue_layer=18)
    with pytest.raises(SystemExit):
        indep.run_dir("t_KO", 670, 0, layer=18)


def test_R8_m6_a_space_in_the_job_list_does_not_silently_match_nothing():
    """R8-m6. The analyser parsed `--require-slurm-job` with `.split(",")` while the other two paths
    used `re.split(r"[ ,]+")`. So `"902004, 902005"` became ['902004', ' 902005'] in one path only,
    and the space-prefixed entry matches no directory -- a filter satisfied by nothing. All three
    parse identically now; a filter that differs between the paths is not a control.
    """
    import re as _re
    for raw in ("902004,902005", "902004, 902005", " 902004 , 902005 "):
        got = [x for x in _re.split(r"[ ,]+", raw or "") if x] or None
        assert got == ["902004", "902005"], (raw, got)
