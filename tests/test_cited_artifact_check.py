"""A claim citing an artifact that is absent or unusable must fail the guard.

WHY THIS GUARD EXISTS. The plan cites run directories as the evidence for its claims, and a
citation is just a string: a claim whose artifact is missing or excluded reads exactly like a claim
whose artifact is fine. Existence and ADMISSIBILITY are separate checks (§11.2) and this guard does
both.

WHY THE TESTS LOOK LIKE THIS. Two lessons from earlier guards in this sprint are baked in:

  * Every test that asserts success is paired with one that asserts FAILURE. A mutation test run
    against an all-green input measures nothing (§7.5), so the fixtures construct violations.
  * `_roots()` is exercised against a directory layout the test builds, because the ad-hoc version
    of this check hand-listed four output roots and reported 14 missing ids that were simply
    elsewhere. The hand-listing bug happened inside the check written to catch hand-listing bugs.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "src", "boombness"))
import cited_artifact_check as cac  # noqa: E402


def _run(root, name, *, rows=4, done=True, excluded=False, n_failed=0, reason="boom"):
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "results.jsonl"), "w") as fh:
        for i in range(rows):
            fh.write(json.dumps({"prompt_id": f"p{i}"}) + "\n")
    if done:
        with open(os.path.join(d, "DONE.json"), "w") as fh:
            json.dump({"schema": "DONE/1", "status": "ok", "rows_written": rows}, fh)
    with open(os.path.join(d, "summary.json"), "w") as fh:
        json.dump({"failures": {"n_failed": n_failed, "n_attempted": rows + n_failed,
                                "n_succeeded": rows,   # require_done refuses n_succeeded == 0
                                "failure_reasons": ({reason: n_failed} if n_failed else {})}}, fh)
    if excluded:
        with open(os.path.join(root, "..", "EXCLUDED_RUNS.json"), "w") as fh:
            json.dump({"schema": "EXCLUDED/1", "per_experiment": {os.path.basename(root): [name]}}, fh)
    return d


ID_A = "arm_20260828_010203_111"
ID_B = "other_20260828_040506_222"


@pytest.fixture
def env(tmp_path, monkeypatch):
    out = tmp_path / "outputs" / "boombness"
    (out / "expA").mkdir(parents=True)
    (out / "expB").mkdir(parents=True)
    plan = tmp_path / "plan.md"
    monkeypatch.setattr(cac, "OUT_ROOT", str(out))
    monkeypatch.setattr(cac, "PLAN", str(plan))
    monkeypatch.setattr(cac, "MIN_EXPECTED", 0)
    monkeypatch.setattr(cac, "CITED_AS_REFUSED", {})
    return out, plan


def test_run_ids_are_extracted_from_prose(env):
    text = f"see `{ID_A}` and {ID_B}, but not plain_words or 2026 alone"
    assert cac.cited_ids(text) == sorted([ID_A, ID_B])


def test_a_MISSING_citation_FAILS(env):
    out, plan = env
    plan.write_text(f"cites {ID_A}\n")
    assert cac.main() == 1


def test_a_citation_resolved_in_ANY_root_passes(env):
    """The hand-listing bug: the id was in a root the check had not listed."""
    out, plan = env
    _run(str(out / "expB"), ID_A)              # deliberately the SECOND root
    plan.write_text(f"cites {ID_A}\n")
    assert cac.main() == 0


def test_roots_are_enumerated_not_hardcoded(env):
    out, _ = env
    (out / "expC").mkdir()
    assert len(cac._roots()) == 3, "a newly created root must be searched without code changes"


def test_an_INADMISSIBLE_citation_FAILS(env):
    """Exists but unusable — no DONE.json, so require_done refuses it."""
    out, plan = env
    _run(str(out / "expA"), ID_A, done=False)
    plan.write_text(f"cites {ID_A}\n")
    assert cac.main() == 1


def test_an_inadmissible_citation_PASSES_when_documented_as_refused(env, monkeypatch):
    out, plan = env
    _run(str(out / "expA"), ID_A, done=False)
    plan.write_text(f"cites {ID_A}\n")
    monkeypatch.setattr(cac, "CITED_AS_REFUSED", {ID_A: "cited as the negative example in §X"})
    assert cac.main() == 0


def test_the_EMPTY_scan_is_refused(env, monkeypatch):
    """Degenerate pass, inherited from §7.6 rather than rediscovered."""
    out, plan = env
    plan.write_text("a plan citing no run ids at all\n")
    monkeypatch.setattr(cac, "MIN_EXPECTED", 10)
    assert cac.main() == 1


def test_every_shipped_exemption_states_a_reason():
    assert cac.CITED_AS_REFUSED, "the shipped exemption table should not be empty"
    for rid, why in cac.CITED_AS_REFUSED.items():
        assert isinstance(why, str) and len(why.strip()) > 20, f"{rid} has no real reason"


def test_the_shipped_floor_is_not_zero():
    assert cac.MIN_EXPECTED >= 10


def test_the_real_repo_passes():
    assert cac.main() == 0


def test_a_cited_run_WITH_FAILURES_is_unclassified_and_FAILS(env):
    """check_run_readable does not inspect n_failed, so guard 8 passed an attrited citation on
    its first day. The count alone cannot decide it -- n_failed means different things in
    different experiments -- so the run must be CLASSIFIED, not thresholded."""
    out, plan = env
    _run(str(out / "expA"), ID_A, n_failed=22, reason="OutOfMemoryError")
    plan.write_text(f"cites {ID_A}\n")
    assert cac.main() == 1


def test_a_cited_run_with_failures_PASSES_once_classified(env, monkeypatch):
    out, plan = env
    _run(str(out / "expA"), ID_A, n_failed=22, reason="OutOfMemoryError")
    plan.write_text(f"cites {ID_A}\n")
    monkeypatch.setattr(cac, "CITED_WITH_FAILURES",
                        {ID_A: "GENUINELY ATTRITED: cited only as the superseded baseline"})
    assert cac.main() == 0


def test_a_clean_run_needs_no_classification(env):
    out, plan = env
    _run(str(out / "expA"), ID_A, n_failed=0)
    plan.write_text(f"cites {ID_A}\n")
    assert cac.main() == 0


def test_every_shipped_failure_classification_states_a_reason():
    """The count carries no meaning; the reason does. An exemption recording only that someone
    looked, without what they concluded, leaves the next reader unable to tell a deliberate
    refusal-citation from a structural artifact."""
    assert cac.CITED_WITH_FAILURES
    for rid, why in cac.CITED_WITH_FAILURES.items():
        assert isinstance(why, str) and len(why.strip()) > 30, f"{rid} has no real reason"


# --- the exemption tables' REASON STRINGS, mechanised ---------------------------------------
#
# A peer's exemption table asserted five sub-corrections "propagated individually"; it was untrue
# and sat inside the table whose purpose is recording CHECKED reasoning. Mine then turned out to
# assert of an attrited run that "no live claim rests on" it, which was also false (§11.10).
#
# Re-verifying once leaves the NEXT reason equally unaudited -- which is how theirs survived. So the
# checkable parts are checked mechanically here, and THE UNCHECKABLE ONES ARE ENUMERATED, because a
# table where you cannot tell the audited entries from the unaudited ones is worse than a smaller
# one. Their framing, adopted.

def test_every_CITED_AS_REFUSED_run_is_actually_refused():
    """The claim 'this run is refused' is mechanically checkable. Check it."""
    import asr_protocol as ap
    for rid in cac.CITED_AS_REFUSED:
        d = cac.resolve(rid)
        assert d, f"{rid} is exempted but does not exist"
        raised = False
        try:
            ap.check_run_readable(d)
        except Exception:
            raised = True
        assert raised, f"{rid} is exempted AS REFUSED but check_run_readable accepts it"


def test_every_CITED_WITH_FAILURES_count_matches_the_ledger():
    """Reasons quote counts like '48/96' and '22 of 40'. Those are checkable against the artifact."""
    import json as _json, os as _os, re as _re
    for rid, why in cac.CITED_WITH_FAILURES.items():
        d = cac.resolve(rid)
        assert d, f"{rid} is classified but does not exist"
        led = (_json.load(open(_os.path.join(d, "summary.json"))).get("failures") or {})
        m = _re.search(r"(\d+)\s*(?:/|of)\s*(\d+)", why)
        assert m, f"{rid}: the reason quotes no count, so nothing can be checked"
        assert int(m.group(1)) == int(led.get("n_failed") or 0), f"{rid}: n_failed disagrees"
        assert int(m.group(2)) == int(led.get("n_attempted") or 0), f"{rid}: n_attempted disagrees"


def test_every_CITED_WITH_FAILURES_reason_names_a_real_failure_reason():
    """The reason string names a ledger key ('family_missing_one_side'); it must actually be there."""
    import json as _json, os as _os
    for rid, why in cac.CITED_WITH_FAILURES.items():
        d = cac.resolve(rid)
        keys = list((_json.load(open(_os.path.join(d, "summary.json"))).get("failures") or {})
                    .get("failure_reasons") or {})
        assert keys, f"{rid}: classified as having failures but the ledger records no reason"
        # ledger keys take two shapes: a bare reason ("family_missing_one_side") and a compound
        # "<query_kind>:<ErrorType>:<message>". The reason must name SOME component, so that a
        # human sentence is linkable back to the artifact's own vocabulary.
        parts = [p for p in keys[0].split(":") if len(p) > 3]
        assert any(p in why for p in parts), (
            f"{rid}: reason names none of the ledger's own tokens {parts!r}")


#: Claims in the exemption tables that CANNOT be checked from artifacts -- assertions about
#: DOWNSTREAM USAGE ("cited only as", "no live claim rests on"). §11.10 is the proof that this is
#: where both sessions' tables were wrong. Enumerated so the suite is never silent about which
#: entries it does not cover.
UNMECHANISABLE = {
    "ab_C_20260819_002240_1397246": "that it is cited INSIDE §0.2.5 as that section's negative example",
    "w640_20260827_224651_3802479": "that its section heading frames it as a refusal",
    "REPRO_bridge_20260826_050914_1018899": "that 48/96 is STRUCTURAL rather than a fault",
    "capNE2_20260827_210525_3544980": "that the rows remain usable despite the config confound",
    "leak2_20260827_212632_3593613": "that the failure IS the probe's finding",
    "q9A_lpQ14B_fc_20260828_104610_2283895": "which sections still present it as a live result",
}


def test_the_unmechanisable_claims_are_ENUMERATED_not_merely_absent():
    """Silence about which entries are unaudited is how a false reason survives."""
    covered = set(cac.CITED_AS_REFUSED) | set(cac.CITED_WITH_FAILURES)
    assert set(UNMECHANISABLE) <= covered, "an enumerated entry is not in either table"
    for rid in covered:
        assert rid in UNMECHANISABLE, (
            f"{rid} has no entry in UNMECHANISABLE: state what about it cannot be checked, "
            "even if that is 'nothing'")


# --- cautioned figures: quoting the governed number requires its caveat -----------------------
#
# A peer flagged that §11.13's clean result on ci95_NOTE held only because no crossbank CI happened
# to be quoted -- safe by accident of what got written, not by construction. These pin the rule that
# replaces the accident.

def test_quoting_a_cautioned_figure_WITHOUT_its_caveat_FAILS(env, monkeypatch):
    out, plan = env
    _run(str(out / "expA"), ID_A)
    monkeypatch.setattr(cac, "CAUTIONED_FIGURES",
                        {"x": (r"\bci95\b", "t_ci95", "quote the t-interval")})
    plan.write_text(f"cites {ID_A}. The ci95 was 0.12 to 0.44.\n")
    assert cac.main() == 1, "a governed figure quoted without its caveat must fail"


def test_quoting_it_WITH_the_caveat_passes(env, monkeypatch):
    out, plan = env
    _run(str(out / "expA"), ID_A)
    monkeypatch.setattr(cac, "CAUTIONED_FIGURES",
                        {"x": (r"\bci95\b", "t_ci95", "quote the t-interval")})
    plan.write_text(f"cites {ID_A}. The t_ci95 was 0.12 to 0.44 (percentile is anticonservative).\n")
    assert cac.main() == 0


def test_not_quoting_the_figure_at_all_passes(env, monkeypatch):
    """The 11.13 situation: the caveat is correctly absent because the figure is."""
    out, plan = env
    _run(str(out / "expA"), ID_A)
    monkeypatch.setattr(cac, "CAUTIONED_FIGURES",
                        {"x": (r"\bci95\b", "t_ci95", "quote the t-interval")})
    plan.write_text(f"cites {ID_A}. No confidence interval is quoted anywhere.\n")
    assert cac.main() == 0


def test_every_shipped_cautioned_figure_states_why():
    assert cac.CAUTIONED_FIGURES
    for label, tup in cac.CAUTIONED_FIGURES.items():
        assert len(tup) == 3, f"{label}: expected (regex, phrase, why)"
        assert isinstance(tup[2], str) and len(tup[2].strip()) > 30, f"{label} has no real reason"


# --- cited artifact FILES (not just run dirs) -------------------------------------------------
#
# Guard 8 was built around run directories. 15 artifact .json paths are cited in the real plan, 12
# inside run dirs and 3 standalone -- and the standalone ones were never checked. All three existed,
# so the gap was harmless at the moment it was found, which is the safe-by-accident state §11.14
# exists to replace.

def test_a_cited_artifact_FILE_that_is_missing_FAILS(env, monkeypatch):
    out, plan = env
    _run(str(out / "expA"), ID_A)
    monkeypatch.setattr(cac, "ROOT", str(out.parent.parent))
    plan.write_text(f"cites {ID_A} and outputs/boombness/nope/absent_thing.json\n")
    assert cac.main() == 1


def test_a_cited_artifact_FILE_that_exists_passes(env, monkeypatch, tmp_path):
    import json as _json
    out, plan = env
    _run(str(out / "expA"), ID_A)
    real = out / "expA" / "real_artifact.json"
    real.write_text(_json.dumps({"ok": True}))
    monkeypatch.setattr(cac, "ROOT", str(tmp_path))
    rel = os.path.relpath(str(real), str(tmp_path))
    plan.write_text(f"cites {ID_A} and {rel}\n")
    assert cac.main() == 0


def test_the_real_plans_artifact_files_all_exist():
    """15 cited .json paths, 12 inside run dirs and 3 standalone -- none missing."""
    import re as _re
    text = open(cac.PLAN, encoding="utf-8").read()
    paths = sorted(set(cac.ARTIFACT_PATH.findall(text)))
    assert len(paths) >= 10, "the artifact-path scanner found suspiciously few paths"
    for q in paths:
        assert os.path.exists(os.path.join(cac.ROOT, q)), f"cited artifact file missing: {q}"


def test_the_caveat_must_be_NEAR_the_figure_not_merely_present(env, monkeypatch):
    """Presence anywhere in a 5,000-line document is not accompaniment.

    Every required phrase already appeared somewhere in the real plan, because §11.13 and §11.14
    discuss these caveats by name. So a figure quoted in a future section would have passed on the
    strength of a paragraph elsewhere explaining that it must not.
    """
    out, plan = env
    _run(str(out / "expA"), ID_A)
    monkeypatch.setattr(cac, "CAUTIONED_FIGURES",
                        {"x": (r"\bci95\b", "t_ci95", "quote the t-interval")})
    monkeypatch.setattr(cac, "CAUTION_WINDOW", 2)
    far = "\n".join([f"cites {ID_A}", "the ci95 was 0.12 to 0.44"] + ["filler"] * 10 + ["t_ci95 is the right one"])
    plan.write_text(far + "\n")
    assert cac.main() == 1, "a caveat 12 lines away does not accompany the figure"


def test_the_caveat_within_the_window_passes(env, monkeypatch):
    out, plan = env
    _run(str(out / "expA"), ID_A)
    monkeypatch.setattr(cac, "CAUTIONED_FIGURES",
                        {"x": (r"\bci95\b", "t_ci95", "quote the t-interval")})
    monkeypatch.setattr(cac, "CAUTION_WINDOW", 2)
    plan.write_text(f"cites {ID_A}\nthe ci95 was 0.12-0.44\nreported as t_ci95, not the percentile\n")
    assert cac.main() == 0


def test_required_phrases_are_DISTINCTIVE_not_common_words():
    """A peer's C-47: a required word matching six unrelated occurrences passes without evidence.

    Distinctive phrasing is necessary and not sufficient -- proximity is the other half -- but a
    common word makes the check vacuous whatever the window.
    """
    text = open(cac.PLAN, encoding="utf-8").read().lower()
    for label, (_fig, phrase, _why) in cac.CAUTIONED_FIGURES.items():
        n = text.count(phrase.lower())
        assert n <= 8, (
            f"{label}: required phrase {phrase!r} occurs {n} times; a common phrase satisfies the "
            "guard without evidence the caveat was stated")


def test_the_shipped_CAUTION_WINDOW_is_a_real_window():
    """The proximity tests monkeypatch the window, so nothing pinned the SHIPPED value.

    A mutant widening it to 100000 passed every other test -- proximity present in the code and
    absent in effect. This is the same omission as the MIN_EXPECTED floor, repeated in the guard
    written after it.
    """
    hi = max(cac.CALIBRATION_DISTANCES)
    assert hi >= 1, "the calibration set records no real separation to calibrate against"
    assert hi < cac.CAUTION_WINDOW <= 3 * hi, (
        f"CAUTION_WINDOW={cac.CAUTION_WINDOW} is not derived from the measured pairings "
        f"{cac.CALIBRATION_DISTANCES}: it must exceed the largest correct distance ({hi}) and stay "
        "within 3x it. The first value, 12, was chosen by eye and was 4x the largest correct "
        "distance -- permissive by construction, with the calibration data available the whole time.")
