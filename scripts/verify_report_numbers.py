#!/usr/bin/env python
"""verify_report_numbers.py — machine-check every gate-table number against its artifact.

THE STANDING BAR, MADE EXECUTABLE. This project's rule is: *"every number in the final report must be
regenerable by a committed script from a committed artifact. If you cannot point at the script and the
artifact, the number does not go in."* That rule has been enforced by reading, and reading has failed
repeatedly — R-13's incremental table matched no artifact in any commit, and nobody noticed for weeks.

This asserts each headline claim against the JSON it comes from. It does NOT recompute the statistics
(the analysis scripts own those); it checks that the number quoted in the deliverable is the number in
the artifact, that the artifact is committed, and that the report actually contains the string.

Exit 1 on any mismatch, so it can gate a commit the way `retraction_sweep.py` does.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, "reports", "boombness_objective_sprint_report.md")

# (label, artifact, json path, expected, tol, a string that must appear in the report)
CHECKS = [
    ("G1 demos_only L18 frac_of_span", "g1_wholeanswer_sow.json",
     ["G1", "pairs", "harm_ctx", "arms", "transplant|demos_only|L18", "frac_of_span"],
     0.689, 0.002, "+68.9%"),
    ("G1 query_only L18 frac_of_span", "g1_wholeanswer_sow.json",
     ["G1", "pairs", "harm_ctx", "arms", "transplant|query_only|L18", "frac_of_span"],
     -0.570, 0.002, "−57.0%"),
    ("G2 POWERED within-domain rho", "g2_analysis_POWER.json",
     ["clustered_inference", "rho_within_domain"], -0.0660, 0.001, "−0.066"),
    ("G2 POWERED permutation p", "g2_analysis_POWER.json",
     ["clustered_inference", "p_perm_within_domain_rho"], 0.4933, 0.002, "0.493"),
    ("G3 all_layers_demo delta", "g3_wholeanswer_block24.json",
     ["G3", "arms", "all_layers_demo", "delta_mean"], -13.437, 0.01, "75.2%"),
    ("G3 deletion ceiling", "g3_wholeanswer_block24.json",
     ["G3", "arms", "no_demo_text", "delta_mean"], -17.879, 0.01, "75.2%"),
    ("14-B arm B clustered delta", "advbench_decomposition.json",
     ["paired_vs_baseline", "B", "delta_cluster_mean"], 0.0305, 0.0005, "+0.0305"),
    ("14-B arm B p_cl", "advbench_decomposition.json",
     ["paired_vs_baseline", "B", "p_cl"], 0.0089, 0.0005, "0.0089"),
    ("14-B control is inert", "advbench_decomposition.json",
     ["paired_vs_baseline", "Bctrl", "delta_cluster_mean"], -0.0062, 0.0005, "−0.0062"),
    ("14-SA super-additivity", "advbench_decomposition.json",
     ["super_additivity", "excess"], 0.0333, 0.0005, "+0.0333"),
    ("14-SA vs control, paired", "advbench_decomposition.json",
     ["super_additivity_vs_control", "excess_real_minus_control"], 0.0268, 0.0005, "+0.0268"),
    ("14-L L12 is the profile max", "advbench_layer_profile.json",
     ["paired_vs_baseline", "L12", "delta_cluster_mean"], 0.0322, 0.0005, "+0.0322"),
    ("14-L L16 is exactly zero", "advbench_layer_profile.json",
     ["paired_vs_baseline", "L16", "delta_cluster_mean"], 0.0000, 1e-9, "+0.0000"),
    ("14-D d_naive reproduces", "advbench_direction_specificity.json",
     ["paired_vs_baseline", "d_naive", "delta_cluster_mean"], 0.0449, 0.0005, "+0.0449"),
    ("14-D d_context is null", "advbench_direction_specificity.json",
     ["paired_vs_baseline", "d_context", "p_cl"], 0.3991, 0.002, "0.399"),
    ("cos(d_surface, d_naive) @L8", "direction_cosines.json",
     ["by_layer", "8", "d_naive"], 0.9452, 0.001, "0.945"),
    ("cos(d_surface, d_context) @L8", "direction_cosines.json",
     ["by_layer", "8", "d_context"], 0.1884, 0.001, "0.188"),
]


def dig(obj, path):
    for k in path:
        if isinstance(obj, list):
            obj = obj[int(k)]
        else:
            obj = obj[k]
    return obj


def committed(rel: str) -> bool:
    r = subprocess.run(["git", "ls-files", "--error-unmatch", rel],
                       cwd=ROOT, capture_output=True)
    return r.returncode == 0


def main() -> int:
    report = open(REPORT, encoding="utf-8").read()
    bad = 0
    print(f"{'claim':<34}{'artifact':<38}{'expected':>11}{'actual':>13}  verdict")
    for label, art, path, expected, tol, needle in CHECKS:
        rel = os.path.join("outputs", "boombness", art)
        full = os.path.join(ROOT, rel)
        if not os.path.exists(full):
            print(f"{label:<34}{art:<38}{'':>11}{'':>13}  ARTIFACT MISSING"); bad += 1; continue
        if not committed(rel):
            print(f"{label:<34}{art:<38}{'':>11}{'':>13}  NOT COMMITTED"); bad += 1; continue
        try:
            actual = float(dig(json.load(open(full)), path))
        except Exception as e:
            print(f"{label:<34}{art:<38}{'':>11}{'':>13}  PATH ERROR {type(e).__name__}")
            bad += 1; continue
        ok_val = abs(actual - expected) <= tol
        ok_txt = needle in report
        verdict = "ok" if (ok_val and ok_txt) else (
            "VALUE MISMATCH" if not ok_val else f"NOT IN REPORT: {needle!r}")
        if verdict != "ok":
            bad += 1
        print(f"{label:<34}{art:<38}{expected:>11.4f}{actual:>13.4f}  {verdict}")
    print()
    if bad:
        print(f"[verify] {bad} of {len(CHECKS)} checks FAILED — a report number does not match its "
              f"artifact, or its artifact is not committed, or the report no longer contains it.")
        return 1
    print(f"[verify] all {len(CHECKS)} gate-table numbers match their committed artifacts "
          f"and appear in the report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
