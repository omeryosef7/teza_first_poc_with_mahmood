"""Every run id cited in MY plan and deliverable must resolve, and be usable or classified.

The concurrent session's `cited_artifact_check` (check_all guard #8) reads a hardcoded PLAN constant
pointing at THEIR plan. Its green on my commits says nothing about my citations — the second guard of
theirs with that property, after `ledger_propagation_check`. They confirmed it rather than leave me to
find out, and the module's `cited_ids`/`resolve`/`_roots` are generic, so this applies them here.

Two failure classes, following R-126's three-layer rule:
  * MISSING      — a cited id that resolves nowhere across all enumerated roots (search space)
  * INADMISSIBLE — an id that resolves to a run with failures or attrition (admissibility)

Absence of a classification is the failure, not the citation itself: a run may be cited precisely
BECAUSE it was refused (C-38, C-42, R-107 all cite attrited runs as documented examples), so the
exemption table records why each is legitimate.
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))
import cited_artifact_check as cac  # noqa: E402

PLAN = os.path.join(ROOT, "external_md",
                    "DEMONSTRATION_RETRIEVAL_BEHAVIORAL_CAUSALITY_NEXT_PHASE_PLAN_AND_PROGRESS.md")
DELIVERABLE = os.path.join(ROOT, "reports", "SPRINT_SUMMARY_2026-08-25_BEHAVIORAL_CAUSALITY.md")

#: Cited ids whose run carries failures, each with the reason the citation is still sound.
#: `n_failed` does NOT mean the same thing in every experiment — the FailureLedger counts whatever
#: that experiment declared a failed unit, so the reason string matters more than the count.
#: Cited ids that appear in outputs/boombness/EXCLUDED_RUNS.json, with why the citation is sound.
#: Membership is tested by EXACT run_id. An earlier ad-hoc substring match false-positived on
#: ...2201570, which is the SUPERSEDOR named in the excluded run's `superseded_by` field, not an
#: excluded run itself — the same over-matching class as every other hand-rolled check this sprint.
EXCLUDED_BUT_CITED = {
    "rederive10_20260825_002905_2199605":
        "reason=no_done_json. Cited at plan L1651 AS the run that died; the claim rests on its "
        "supersedor rederive10_20260825_002934_2201570, which is not excluded.",
}

CLASSIFIED = {
    # --- cited BECAUSE they were refused; the refusal is the point being made ---
    "q5A_lpQ14B_20260828_083233_2269491":
        "attrited 68/160 (OOM). Cited by C-38 and C-42 as the population that must be refused.",
    "q9A_lpQ14B_fc_20260828_104610_2283895":
        "attrited 18/40. Cited by R-107 as the run my R-105 guard refuses.",
    # --- 'failures' are the artifact's intended output, not run failures ---
    "five_unmeasured_20260828_135856_1747482":
        "margin_exposure run whose 5 'failures' are borrowed_scale REFUSALS it was invoked to emit.",
    # --- 'failures' are a documented structural property of the bank, per C-24 ---
    "bridge_20260825_101613_3117657":
        "144/288 family_missing_one_side: C-24's finding that the probe exists for core2x2 only.",
    "qbridge_20260825_104155_3190213":
        "same, Qwen3 side.",
    "REPRO_R16_20260826_051035_1020533":
        "same, reproduction run.",
}


def _audit(text):
    missing, unclassified = [], []
    for rid in sorted(set(cac.cited_ids(text))):
        d = cac.resolve(rid)
        if not d:
            missing.append(rid)
            continue
        s = os.path.join(d, "summary.json")
        if not os.path.exists(s):
            continue
        try:
            sm = json.load(open(s))
        except Exception:
            continue
        f = sm.get("failures") or {}
        nb, nr = sm.get("n_bank_rows"), sm.get("n_result_rows")
        bad = bool(f.get("n_failed")) or (nb is not None and nr is not None and nr < nb)
        if bad and rid not in CLASSIFIED:
            unclassified.append(rid)
    return missing, unclassified


def _excluded_ids():
    """Exact run_ids from the repo's exclusion record — never substring matching."""
    p = os.path.join(ROOT, "outputs", "boombness", "EXCLUDED_RUNS.json")
    if not os.path.exists(p):
        return {}
    d = json.load(open(p))
    return {r["run_id"]: r.get("reason") for r in d.get("runs", []) if r.get("run_id")}


def test_no_cited_run_is_silently_excluded_or_unfinished():
    """The complementary gap to the attrition check, and the one their guard catches that mine did not.

    `check_run_readable` refuses ABORTED / missing-DONE / EXCLUDED_RUNS and does NOT inspect
    attrition; `_audit` above inspects attrition and did NOT inspect these. Each check missed exactly
    what the other caught, which is why both are here.
    """
    exc = _excluded_ids()
    for path in (PLAN, DELIVERABLE):
        text = open(path, encoding="utf-8").read()
        cited = set(cac.cited_ids(text))
        bad = sorted((cited & set(exc)) - set(EXCLUDED_BUT_CITED))
        assert not bad, (
            f"{os.path.basename(path)} cites EXCLUDED runs without classification: "
            f"{[(b, exc[b]) for b in bad]}")
        unfinished = []
        for rid in sorted(cited):
            d = cac.resolve(rid)
            if d and not os.path.exists(os.path.join(d, "DONE.json")) \
                    and rid not in EXCLUDED_BUT_CITED:
                unfinished.append(rid)
        assert not unfinished, f"{os.path.basename(path)} cites unfinished runs: {unfinished}"


def test_exclusion_membership_is_exact_not_substring():
    """Pins the false positive that prompted this test.

    A two-way substring match reports the supersedor as excluded, because its id appears inside the
    excluded run's `superseded_by` field. Exact run_id membership does not.
    """
    exc = _excluded_ids()
    assert "rederive10_20260825_002905_2199605" in exc
    assert "rederive10_20260825_002934_2201570" not in exc


def test_every_cited_run_id_resolves():
    for path in (PLAN, DELIVERABLE):
        missing, _ = _audit(open(path, encoding="utf-8").read())
        assert not missing, f"{os.path.basename(path)} cites unresolvable run ids: {missing}"


def test_every_failing_cited_run_is_classified():
    for path in (PLAN, DELIVERABLE):
        _, unclassified = _audit(open(path, encoding="utf-8").read())
        assert not unclassified, (
            f"{os.path.basename(path)} cites runs with failures that are not classified: "
            f"{unclassified}. Add a CLASSIFIED entry saying why the citation is sound, "
            f"or stop citing the run.")


def test_the_audit_can_actually_fail():
    """A check run only against passing input measures nothing (their mutation lesson)."""
    missing, _ = _audit("see run notarealrun_20260828_010101_999999 for details")
    assert missing == ["notarealrun_20260828_010101_999999"]


def test_it_finds_the_real_citations_and_not_zero_of_them():
    """Guards the degenerate pass: a regex matching nothing also reports no problems."""
    ids = set(cac.cited_ids(open(PLAN, encoding="utf-8").read()))
    assert len(ids) >= 40, f"only extracted {len(ids)} run ids from the plan"
    assert "c5A_tb_b1_20260828_125009_2294147" in ids      # the C5 batch-1 rerun
    assert "q5A_lpQ14B_20260828_083233_2269491" in ids     # the refused-attrited citation
