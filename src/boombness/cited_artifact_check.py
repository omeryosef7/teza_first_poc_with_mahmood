"""cited_artifact_check.py — a run id cited in the deliverable that does not exist, or must not be used.

WHY. The plan document cites run directories as the evidence for its claims. Nothing checked that
those directories still exist, or that they pass the admissibility rules this sprint spent days
building. A claim whose artifact is missing or excluded reads exactly like a claim whose artifact is
fine — the citation is a string.

This is the §11.4 deep-review check, promoted from an ad-hoc script into a guard, for the reason
that check itself demonstrated: **run once by hand it found nothing; the value is in it running
every time.**

THE HAND-LISTING BUG THIS MODULE WAS BORN FROM. The first version of that ad-hoc check searched
FOUR output roots, chosen from memory, and reported **14 missing run ids**. Widening to all 36
roots gave **0 missing** — every id was in an experiment directory I had not listed. So the
hand-listing failure happened *inside the check written to catch hand-listing failures*, and the
only thing that stopped it becoming a false claim in a deep-review section was that 14 was
implausible enough to re-run. **Implausibility is not a control.**

Hence the rule this module enforces on itself: **enumerate the SEARCH SPACE, not just the row set.**
`_roots()` globs every directory under the output root; it never names one.

ADMISSIBILITY vs EXISTENCE are separate, per §11.2. A cited run may exist and still be unusable —
partial, excluded, gate-failed. Both are checked, and a run may be cited as a *documented negative
example* (this sprint cites two), so `CITED_AS_REFUSED` names those with a reason. Silence is not
allowed; that is §7.5's rule applied to artifacts.

Reads directory metadata only. No model, no generations, no network.
"""
from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PLAN = os.path.join(ROOT, "external_md", "BOOMBNESS_RESEARCH_VALIDATION_AND_OBJECTIVE_PLAN.md")
OUT_ROOT = os.path.join(ROOT, "outputs", "boombness")

sys.path.insert(0, HERE)

#: Run ids deliberately cited as examples of runs that MUST NOT be used. The value is the reason and
#: is required — an unexplained exemption is the silence this guard exists to prevent.
CITED_AS_REFUSED = {
    "ab_C_20260819_002240_1397246":
        "cited INSIDE §0.2.5 as the 482-row partial that the first corpus sweep wrongly ingested "
        "and reported under the complete run's tag; it is the negative example of that section",
    "w640_20260827_224651_3802479":
        "cited under §0.12, whose heading reads 'and my own guard refused it' — the run is the "
        "subject of a refusal, not the evidence for a claim",
}

#: RULE FOR THESE REASON STRINGS, learned by writing a bad one: **quote the artifact's own tokens,
#: do not paraphrase them.** The q9A reason originally said "lost to OOM" against a ledger key of
#: `semantic_forced_choice:OutOfMemoryError:...`. That sentence was true, and no mechanical check
#: could ever bind it to the artifact, because the vocabulary did not match. A peer named it as a
#: third variant of the unauditable-prose class: not false, not unverifiable, but written so that
#: nothing can verify it. `test_every_CITED_WITH_FAILURES_reason_names_a_real_failure_reason`
#: enforces the rule.
#:
#: Cited runs whose ledger records FAILURES. `check_run_readable` does NOT inspect `n_failed` — it
#: refuses ABORTED, missing-DONE and EXCLUDED runs only — so guard 8 passed an attrited citation on
#: its first day (`q9A_lpQ14B_fc`, 22 of 40 rows lost to OOM). A peer found the same blind spot on
#: their own corpus and supplied the reason it cannot be fixed with a threshold:
#:
#:   **`n_failed` does not mean the same thing across experiments.** The FailureLedger counts
#:   whatever that experiment declared a failed unit, so the REASON STRING carries the meaning and
#:   the count does not. A naive `n_failed > 0` rule flags structural facts, probe verdicts, and a
#:   tool's own intended refusals as broken citations.
#:
#: So each is classified by what its reason actually means. The value is required: an exemption that
#: records only that someone looked, without recording what they concluded, leaves the next reader
#: unable to tell a deliberate refusal-citation from a bridge artifact.
CITED_WITH_FAILURES = {
    "REPRO_bridge_20260826_050914_1018899":
        "STRUCTURAL: 48/96 `family_missing_one_side` — the forced-choice probe exists for core2x2 "
        "only, so stems outside it have no probe side. A documented property of the bank, not a "
        "failed run",
    "capNE2_20260827_210525_3544980":
        "DOCUMENTED-VALID: 3/4 `config_confounded_but_row_level_valid` — the reason string states "
        "the rows remain usable; the failure marks a config confound, not lost data",
    "leak2_20260827_212632_3593613":
        "PROBE VERDICT: 1/24 `d_surface_not_lexically_clean` is the probe's FINDING about a "
        "direction, emitted through the ledger; the run did what it was asked",
    "q9A_lpQ14B_fc_20260828_104610_2283895":
        "GENUINELY ATTRITED: 22/40 lost to OutOfMemoryError (CUDA out of memory). §5.19 re-measured the contrast on qbA/qbD (40/40) "
        "and §5.18.1 withdrew the one-sample claim. CORRECTED 2026-08-28: an earlier version of this "
        "reason asserted 'no live claim rests on this run', which was FALSE — it is the cited "
        "artifact for §5.18's headline binding row, and that row carried no in-place supersession "
        "marker. The row is now struck through and re-pointed at qbA/qbD. This entry is the reason "
        "strings' own EXEMPT[3]: an assertion inside the table whose purpose is recording CHECKED "
        "reasoning, which had not been checked",
    "w640_20260827_224651_3802479":
        "TOOL'S OWN REFUSAL: 1/1 `not_sprint_grade` is arm_report refusing the arm, which is the "
        "artifact's intended output and the subject of §0.12",
}

#: CAUTIONED FIGURES: an artifact caveat that says "if you quote X, say Y" is inert until someone
#: quotes X — and then it is a live defect with nothing watching for it.
#:
#: §11.13 checked these ONCE and found them all absent, so every caveat was correctly missing. A
#: peer flagged the weakness of that result: `crossbank_knockout_test`'s `ci95_NOTE` is a direct
#: instruction ("percentile bootstrap, ANTICONSERVATIVE at small k -- quote `t_ci95`"), and it was
#: satisfied only because no crossbank CI happened to be quoted. **Safe by accident of what got
#: written, not by construction** — the same shape as a citation being sound only because the claim
#: rested on its supersedor.
#:
#: So the accident is replaced by a rule: quoting the governed figure REQUIRES the caveat's own
#: phrase to appear. Each entry is (regex for the governed figure, phrase that must accompany it).
#: A caveat that names no checkable figure belongs in the prose, not here.
CAUTIONED_FIGURES = {
    "crossbank ci95": (
        r"\bci95\b(?!_NOTE)",
        "t_ci95",
        "crossbank_knockout_test's ci95_NOTE: the percentile bootstrap is ANTICONSERVATIVE at small "
        "k, so a quoted CI must be the t-interval and must say so",
    ),
    "probes best-layer AUROC": (
        r"best_layer_by_auroc|SELECTED_ON_TEST",
        "selected on test",
        "probes' selection_warning: the best layer is the argmax of TEST AUROC over 17 layers with "
        "no validation split, so any such figure is optimistically biased",
    ),
    "rescue percentage": (
        r"rescue[_ ]percent|rescued\s+\d+\s*%",
        "INVERTED",
        "rescue_dissociation_table's PCT_CAVEAT (DR-5): the percentage inverts relative to the "
        "evidence when the clean baseline is near zero",
    ),
}

#: A run id as this repo writes them: <tag>_<YYYYMMDD>_<HHMMSS>_<pid>.
RUN_ID = re.compile(r"\b([A-Za-z0-9_]+_20[0-9]{6}_[0-9]{6}_[0-9]+)\b")

#: The corpus has never cited fewer than this many run ids. A collapse means the SCANNER broke, not
#: that the citations vanished — the degenerate-pass floor from §7.6, which this module inherits
#: rather than rediscovers.
MIN_EXPECTED = 10


def _roots():
    """Every directory under the output root. ENUMERATED, never hand-listed — see module docstring."""
    if not os.path.isdir(OUT_ROOT):
        return []
    return [os.path.join(OUT_ROOT, d) for d in sorted(os.listdir(OUT_ROOT))
            if os.path.isdir(os.path.join(OUT_ROOT, d))]


def _failures(run_dir: str):
    """(n_failed, first reason) from the run's ledger, or (0, "") if it records none."""
    import json
    sp = os.path.join(run_dir, "summary.json")
    if not os.path.isfile(sp):
        return 0, ""
    try:
        f = (json.load(open(sp)).get("failures") or {})
    except Exception:
        return 0, ""
    reasons = list(f.get("failure_reasons") or {})
    return int(f.get("n_failed") or 0), (reasons[0][:48] if reasons else "")


def cited_ids(text: str):
    return sorted(set(RUN_ID.findall(text)))


def resolve(run_id: str, roots=None):
    """The directory a cited id refers to, or None. Searches every root."""
    for r in (roots if roots is not None else _roots()):
        p = os.path.join(r, run_id)
        if os.path.isdir(p):
            return p
    return None


def main() -> int:
    if not os.path.isfile(PLAN):
        print("[cited-artifact] plan missing; nothing to check")
        return 0
    import asr_protocol as ap

    ids = cited_ids(open(PLAN, encoding="utf-8").read())
    roots = _roots()

    if len(ids) < MIN_EXPECTED:
        print(f"[cited-artifact] FAIL — only {len(ids)} run ids found in the plan, expected at "
              f"least {MIN_EXPECTED}. The scanner has broken; a guard that checks nothing must not "
              f"report success.")
        return 1

    missing, inadmissible, unclassified, ok = [], [], [], 0
    for rid in ids:
        d = resolve(rid, roots)
        if d is None:
            missing.append(rid)
            continue
        try:
            ap.check_run_readable(d)
        except Exception as e:                      # noqa: BLE001 — any refusal is a refusal
            if rid in CITED_AS_REFUSED:
                ok += 1
            else:
                inadmissible.append((rid, os.path.basename(os.path.dirname(d)), str(e)[:70]))
            continue
        nf, why = _failures(d)
        if nf and rid not in CITED_WITH_FAILURES:
            unclassified.append((rid, nf, why))
        else:
            ok += 1

    # CAUTIONED FIGURES: quoting a governed figure requires its caveat phrase (see the table).
    plan_text = open(PLAN, encoding="utf-8").read()
    caution_fail = []
    for label, (fig_re, phrase, why) in CAUTIONED_FIGURES.items():
        if re.search(fig_re, plan_text, re.I) and phrase.lower() not in plan_text.lower():
            caution_fail.append((label, phrase, why))

    print(f"[cited-artifact] {len(ids)} run ids cited across {len(roots)} enumerated roots; "
          f"{ok} usable or documented-refused; {len(CAUTIONED_FIGURES)} cautioned figures watched")
    for label, phrase, why in caution_fail:
        print(f"  CAUTIONED FIGURE QUOTED WITHOUT ITS CAVEAT [{label}]: expected {phrase!r}")
        print(f"      {why}")
    for rid in missing:
        print(f"  MISSING {rid}: cited in the plan, found in none of the {len(roots)} roots")
    for rid, root, why in inadmissible:
        print(f"  INADMISSIBLE {rid} (in {root}): {why}")
        print(f"      -> fix the claim, or add {rid} to CITED_AS_REFUSED with a reason")
    for rid, nf, why in unclassified:
        print(f"  UNCLASSIFIED FAILURES {rid}: n_failed={nf} ({why})")
        print(f"      -> classify it in CITED_WITH_FAILURES with what the reason MEANS, or fix the claim")
    if missing or inadmissible or unclassified or caution_fail:
        print("[cited-artifact] FAIL — a claim cites an artifact that is absent or unusable.")
        return 1
    print("[cited-artifact] every cited artifact exists and is usable or documented-refused")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
