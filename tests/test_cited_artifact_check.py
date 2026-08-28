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
