"""canonical_figures.py — one number, one source, checked in every deliverable that quotes it.

WHY. Three times in one week the actual defect was "two deliverables that must agree, updated one at
a time":
  * arm F struck in the full report and still live in the short update (R-20);
  * the band edges corrected in one and not the other (~L6-L12 vs ~L6-L14);
  * the section-13 scoring rescored in the report, still three retractions old in the short update.
That is structurally the SAME failure as a flag threaded into one of two code paths -- the bug class
this project has hit eight times in source -- and nothing was checking for it in prose.

This is a FIGURE REGISTRY. Each entry names a headline number, the artifact that produces it, and how
it is written. The check then verifies that every deliverable quoting that figure quotes the SAME
value, and that the value still matches its artifact.

DELIBERATELY NARROW. It does not parse claims or attempt to understand prose -- that is the semantic
problem `population_index` declined for the same reason. It checks a curated list of numbers that
have already caused a disagreement or would be expensive to get wrong. A registry of ten figures that
is correct beats a parser of a hundred that is not.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
import sys

DELIVERABLES = [
    "reports/boombness_objective_sprint_report.md",
    "reports/boombness_objective_sprint_short_update.md",
]

#: name -> (regex that captures the value as group 1, artifact glob, json path, tolerance)
#: The regex must be specific enough that a match IS a quotation of this figure.
FIGURES = {
    "advbench_band_mean": (
        r"5-draw control band\D{0,20}([+-]?0\.\d{3,5})",
        "outputs/boombness/advbench_band.json", ["control_band", "mean"], 5e-4),
    # SCOPE EACH REGEX TO ITS OWN FIGURE. The first version matched any "between-draw sd", which
    # collides with every other band this report legitimately discusses -- ClearHarm's 0.0034, the
    # RETRACTED R-12 band's 0.0048, G4's steering band 0.0301 -- and reported them as disagreements.
    # A registry that cries wolf is worse than none, which is the same lesson the marker-exemption
    # failure taught. The pattern must pin the population it belongs to.
    "advbench_band_sd": (
        # "between-draw" is OPTIONAL: the short update writes "sd 0.0026", the report writes
        # "between-draw sd 0.0026". Requiring the long form made the figure look ABSENT from the short
        # update -- which the new absence check (c) correctly reported on its first run. Still pinned
        # to its own band by the "5-draw control band" prefix, so the over-breadth failure noted above
        # does not return.
        r"5-draw control band[^\n]{0,60}?(?:between-draw )?sd\s*(0\.\d{3,5})",
        "outputs/boombness/advbench_band.json", ["control_band", "between_draw_sd"], 5e-4),
    # E12 (2026-08-21). Registered the same day the result landed, because the figure registry was
    # built precisely for numbers that cross deliverables, and a registry that lags its own results
    # is the phase-board failure in a different costume.
    # Pin the HEADLINE row only. The first pattern also matched the independent-split row (0.6049),
    # which the report legitimately reports beside the headline (0.6117) -- so the registry flagged a
    # table for containing two rows. That is the SECOND time one of these patterns has been too
    # broad (the first conflated every band's between-draw sd). Writing a regex that pins exactly one
    # figure is harder than it looks, and a registry entry that cannot do so should not be added.
    "e12_cross_concept_cos": (
        r"\(bomb-dev vs knife-dev\)[^|]*\|\s*\*\*\+?(0\.6\d{2,3})\*\*",
        "outputs/boombness/e12_concept_swap_cosines.json",
        ["cosines", "d_surface", "mean"], 5e-3),
    "e12_knife_causal_delta": (
        r"`?knife`?-fitted[^\n]{0,80}?\+(0\.01\d{2})",
        "outputs/boombness/e12_causal_knife.json",
        ["groups", "ALL", "delta"], 1e-3),
    "layer_shape_p": (
        r"permutation\D{0,12}p\s*=\s*(0\.0\d{2,4})",
        "outputs/boombness/layer_profile_shape_test.json", ["p_perm"], 2e-3),
}


#: name -> which deliverables MUST quote this figure.
#: WHY THIS EXISTS. Check (a) below compares the values two deliverables quote -- but it only fires
#: when `len(nums) > 1`, i.e. when at least two deliverables quote the figure at all. A figure MISSING
#: from the short update produces exactly one value and passed in silence. So the registry reported
#: "all registered figures agree" on precisely the failure it was built to catch: the short update
#: lagging the report. Detecting disagreement is not detecting absence, and the three incidents in the
#: module docstring were all ABSENCE (a figure struck in one file, still live in the other).
#: Found by the 2026-08-21 audit. Scope must be DECLARED per figure -- inferring it from "how many
#: files happen to quote this today" is the address-by-incidental-property bug this repo has hit four
#: times in one file.
SCOPE_ALL = "all"          # every deliverable in DELIVERABLES must quote it
SCOPE_REPORT_ONLY = "report_only"   # only the full report; must be justified in the comment

FIGURE_SCOPE = {
    "advbench_band_mean": SCOPE_ALL,
    "advbench_band_sd": SCOPE_ALL,
    # E12's two figures are RETRACTED (R-23 behavioural, R-24 representational). They are quoted only
    # in the full report, inside the sections that explain the retraction; the short update never
    # carried the claim and must not acquire it now. Declared report-only for that reason, not
    # because it happens to be where they currently sit.
    "e12_cross_concept_cos": SCOPE_REPORT_ONLY,
    "e12_knife_causal_delta": SCOPE_REPORT_ONLY,
    "layer_shape_p": SCOPE_ALL,
}


def _artifact_value(pat, path):
    hits = sorted(glob.glob(pat)) if pat else []
    if not hits:
        return None
    d = json.load(open(hits[-1]))
    for k in path:
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d if isinstance(d, (int, float)) else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    texts = {}
    for f in DELIVERABLES:
        try:
            texts[f] = open(f, encoding="utf-8").read()
        except OSError:
            pass

    report, problems = {}, []
    for name, (rx, apat, apath, tol) in FIGURES.items():
        quoted = {}
        for f, t in texts.items():
            vals = {m.group(1) for m in re.finditer(rx, t) if m.group(1)}
            if vals:
                quoted[f] = sorted(vals)
        entry = {"regex": rx, "quoted_in": quoted}
        # (a) do the deliverables agree with EACH OTHER?
        allvals = {v for vs in quoted.values() for v in vs}
        nums = sorted({float(v) for v in allvals})
        # Compare NUMERICALLY with the figure's tolerance: 0.0109 and 0.011 are one number written at
        # two precisions, not a disagreement. String equality would have flagged it, and a checker
        # that flags rounding is a checker nobody runs twice.
        t = tol or 1e-9
        if len(nums) > 1 and (max(nums) - min(nums)) > t:
            problems.append(f"{name}: deliverables quote DIFFERENT values {sorted(allvals)} "
                            f"(spread {max(nums)-min(nums):.5f} > tol {t}) "
                            f"-- {', '.join(os.path.basename(k) for k in quoted)}")
        # (b) does the quoted value still match its artifact?
        if apat and allvals:
            av = _artifact_value(apat, apath)
            entry["artifact_value"] = av
            if av is not None:
                for v in allvals:
                    if abs(float(v) - float(av)) > t:
                        problems.append(f"{name}: deliverables quote {v} but "
                                        f"{os.path.basename(apat)} says {av:.5f}")
        # (c) ABSENCE. A figure declared SCOPE_ALL that a deliverable does not quote is a lag, which
        # is the failure mode that motivated this module. Checks (a) and (b) are both silent on it.
        scope = FIGURE_SCOPE.get(name, SCOPE_ALL)
        entry["scope"] = scope
        if scope == SCOPE_ALL:
            for f in texts:
                if f not in quoted:
                    problems.append(f"{name}: declared SCOPE_ALL but NOT QUOTED in "
                                    f"{os.path.basename(f)} -- deliverable lag, or the regex no "
                                    f"longer matches that file's wording")
        elif name not in FIGURE_SCOPE:
            problems.append(f"{name}: no declared scope")
        report[name] = entry

    out = {"figures": report, "problems": problems,
           "note": "a curated registry, not a parser. It checks numbers that have already caused a "
                   "cross-deliverable disagreement or would be expensive to get wrong.",
           "provenance": {"argv": sys.argv,
                          "git_commit": subprocess.run(["git", "rev-parse", "HEAD"],
                                                       capture_output=True, text=True).stdout.strip()}}
    if args.out:
        with open(args.out, "w") as f:
            json.dump(out, f, indent=2)
    for name, e in report.items():
        where = " ".join(f"{os.path.basename(k)}={v}" for k, v in e["quoted_in"].items()) or "(not quoted)"
        av = e.get("artifact_value")
        print(f"  {name:26s} {where}" + (f"   artifact={av}" if av is not None else ""))
    if problems:
        print(f"\n[figures] {len(problems)} PROBLEM(S):")
        for p in problems:
            print(f"   {p}")
    else:
        print("\n[figures] all registered figures agree, and every SCOPE_ALL figure is present in every deliverable")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
