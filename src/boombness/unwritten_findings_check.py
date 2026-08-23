"""unwritten_findings_check.py — which committed artifacts have findings that reach NO deliverable?

WHY. The sprint's recurring failure is not bad analysis, it is analysis that never gets written down.
Three separate times a serious objection was answered by numbers already sitting on disk; last tick,
three of §19's eleven answers were stale while the artifacts correcting them had been committed for
days. `plan_coverage_check` cannot see this -- it checks that plan sections are CITED, and §19 was
"covered" the whole time.

WHY NOT JUST GREP FOR FILENAMES. 53 of 114 artifacts are uncited by name, but that over-counts badly:
a finding can be written up without naming its file, which is true of several sections added this week.
Absence of the filename is not absence of the finding.

WHAT THIS DOES INSTEAD. For each artifact it extracts distinctive NUMBERS -- floats with enough
precision to be fingerprints rather than coincidences -- and asks whether any of them appears in the
report or the short update, at the rounding the report actually uses. An artifact none of whose numbers
appear anywhere is one whose content has not reached a reader.

CALIBRATION, AND THE VERSION THAT DID NOT WORK. v1 tested any 3-or-4-decimal float and counted an
artifact as written up on ONE match. It reported 0 silent artifacts out of 93 -- and the hit histogram
showed 64 of them matching 10+ fingerprints, i.e. the test was saturating on values like 0.5000 and
0.0646 that recur everywhere. A check that cannot go red is not a check, so it was rebuilt on RARE
fingerprints: only values that occur in exactly ONE artifact across the whole corpus are used, which
makes a match evidence about that artifact rather than about the corpus.

A LIMIT OBSERVED IN USE (2026-08-23). `qwen3_armD_natural_doublespeak.json` still reports 0 of 32
rare numbers found AFTER its finding was written into the report. The reason is structural: its
HEADLINE values (0.1595, 0.8881, 0.7738) also occur in sibling Qwen3 artifacts, so the uniqueness
filter excludes exactly the numbers a writer would quote, leaving 32 incidentals (Wilson bounds,
mean_score) that nobody would. So this measures NUMBER presence, not FINDING presence, and it is
biased against artifacts that share a family. Treat a persistent hit on a written-up artifact as noise,
not as an instruction to quote a Wilson bound.

WHAT A HIT MEANS. Not "this must be written up". Infrastructure files (`canonical_figures`,
`population_index`), indexes (`unanalysed_inventory`, this file) and deliberately superseded artifacts
SHOULD be silent. The list is a prompt to decide, one artifact at a time, whether silence was chosen or
merely happened. Those categories are excluded by name so the remainder is short enough to read.
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from unanalysed_inventory import git_commit_safe  # noqa: E402

# Files that SHOULD be silent in the deliverables.
EXEMPT_EXACT = {
    "canonical_figures.json", "population_index.json", "unanalysed_inventory.json",
    "unanalysed_triage.json", "shard_citation_check.json", "unwritten_findings_check.json",
    "replicate_noise.json", "judge_session_drift.json", "multiplicity_families.json",
    "how_to_read_the_p_values.json", "bank_join_recheck.json",
}
EXEMPT_SUBSTR = ("_SUPERSEDED", "_JUDGE_ARTIFACT", "reanalyze_", "_cos.json")

#: Artifacts that are SILENT ON PURPOSE because they are retracted or superseded, with the reason and
#: the artifact that replaced them. Silence here is correct and must not be read as a gap.
#:
#: This list exists because the check pointed me at `clearharm_decomposition.json` and I began writing
#: it up before `retraction_sweep` stopped me: its `ch_*` judge runs carry `goal_status: None` on all
#: 179 rows -- every completion scored against an EMPTY GOAL, retraction R-14. Its numbers are more
#: flattering than the truth (d_surface alone "significant" at +0.1061; super-additivity +0.095), and
#: both claims collapse in the re-judged artifact. A detector that says "this finding never reached a
#: reader" is, for a retracted artifact, saying the system worked.
RETRACTED_ARTIFACTS = {
    "clearharm_decomposition.json":
        "R-14: judged against an empty goal (goal_status None on all 179 rows). "
        "Superseded by clearharm_decomposition_regoal.json.",
}


def numbers_of(obj, out, depth=0):
    """Distinctive floats: 3+ decimals, not 0/1, not obviously an index."""
    if depth > 6:
        return
    if isinstance(obj, dict):
        for v in obj.values():
            numbers_of(v, out, depth + 1)
    elif isinstance(obj, list):
        for v in obj[:200]:
            numbers_of(v, out, depth + 1)
    elif isinstance(obj, float):
        if 1e-6 < abs(obj) < 1e6 and abs(obj) not in (0.0, 1.0):
            out.append(obj)


def fingerprints(vals, k=40):
    """Render each value the way a report would, at 3 and 4 decimals."""
    seen, out = set(), []
    for v in vals:
        for s in (f"{v:.4f}", f"{v:.3f}"):
            if s.endswith("000") or s in seen:
                continue
            seen.add(s)
            out.append(s)
        if len(out) >= k:
            break
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-hits", type=int, default=1,
                    help="an artifact counts as written up if at least this many of its numbers appear")
    ap.add_argument("--min-rare", type=int, default=5,
                    help="below this many artifact-unique fingerprints the test is VACUOUS, not "
                         "evidence of silence, so the artifact is reported separately")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    text = ""
    for p in ("reports/boombness_objective_sprint_report.md",
              "reports/boombness_objective_sprint_short_update.md"):
        try:
            text += io.open(p, encoding="utf-8").read()
        except OSError:
            pass
    # strip thousands separators / markdown so a bare number matches
    hay = text.replace(",", "")

    # PASS 1: fingerprint every artifact, then keep only fingerprints UNIQUE to one artifact.
    per_art, counts = {}, {}
    for p in sorted(glob.glob("outputs/boombness/*.json")):
        b = os.path.basename(p)
        if b in EXEMPT_EXACT or b in RETRACTED_ARTIFACTS or any(s in b for s in EXEMPT_SUBSTR):
            continue
        try:
            blob = json.load(open(p))
        except Exception:
            continue
        vals = []
        numbers_of(blob, vals)
        fps = set(fingerprints(vals, k=400))
        per_art[b] = fps
        for s in fps:
            counts[s] = counts.get(s, 0) + 1

    rows = []
    for b, fps in per_art.items():
        rare = sorted(s for s in fps if counts.get(s) == 1)
        hits = [s for s in rare if s in hay]
        fps = rare
        rows.append({
            "artifact": b,
            "named_in_deliverable": (b in text or b.replace(".json", "") in text),
            "n_rare_fingerprints_tested": len(fps),
            "n_fingerprints_tested": len(fps),
            "n_fingerprints_found": len(hits),
            "example_hits": hits[:5],
            "written_up": (b in text) or (len(hits) >= a.min_hits),
        })

    # A TEST WITH NOTHING TO TEST IS NOT A FAILING TEST. An artifact with fewer than --min-rare
    # artifact-unique numbers cannot be shown silent by this method; calling it silent would
    # manufacture findings out of thin evidence, which is the opposite of the point.
    silent = [r for r in rows
              if not r["written_up"] and r["n_rare_fingerprints_tested"] >= a.min_rare]
    untestable = [r for r in rows
                  if not r["written_up"] and r["n_rare_fingerprints_tested"] < a.min_rare]
    out = {
        "question": "which committed artifacts have findings that reach no deliverable?",
        "method": "fingerprint every artifact's floats at 3 and 4 decimals, keep only fingerprints "
                  "occurring in exactly ONE artifact corpus-wide, and look for those in the report and "
                  "short update. Filename citation also counts.",
        "v1_did_not_work": (
            "v1 used any 3-4 decimal float and counted one match as written-up. It found 0 silent of "
            "93, with 64 artifacts matching 10+ fingerprints -- saturating on values like 0.5000 that "
            "recur everywhere. A check that cannot go red is not a check."),
        "why_not_filenames_alone": "53 of 114 artifacts are uncited by name, but a finding can be "
                                   "written up without naming its file. Absence of the filename is not "
                                   "absence of the finding.",
        "a_hit_is_a_prompt_not_a_verdict": (
            "infrastructure, indexes and deliberately superseded artifacts SHOULD be silent and are "
            "exempted by name. For the rest, this asks whether silence was chosen or merely happened."),
        "exempted": sorted(EXEMPT_EXACT) + [f"*{s}*" for s in EXEMPT_SUBSTR],
        "exempted_because_retracted": RETRACTED_ARTIFACTS,
        "n_artifacts_checked": len(rows),
        "n_silent": len(silent),
        "min_rare_fingerprints_for_a_verdict": a.min_rare,
        "n_untestable_too_few_rare_numbers": len(untestable),
        "untestable": sorted(untestable, key=lambda r: r["artifact"]),
        "silent": sorted(silent, key=lambda r: -r["n_fingerprints_tested"]),
        "all": sorted(rows, key=lambda r: r["artifact"]),
        "provenance": {"argv": sys.argv, "git_commit": git_commit_safe()},
    }
    with open(a.out, "w") as f:
        json.dump(out, f, indent=2)

    print(f"checked {len(rows)} artifacts (infrastructure/indexes/superseded exempted)")
    print(f"SILENT in both deliverables: {len(silent)}  "
          f"(+{len(untestable)} untestable: <{a.min_rare} artifact-unique numbers)\n")
    for r in out["silent"]:
        print(f"  {r['artifact'][:48]:50s} {r['n_fingerprints_found']}/"
              f"{r['n_rare_fingerprints_tested']} rare numbers found")
    print(f"\n[unwritten] -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
