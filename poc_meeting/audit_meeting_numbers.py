"""
Audit script for Mahmood meeting headline numbers.
Reads artifacts from Stage 4, 4.7, and 4.8 and verifies all claims.
Outputs PASS/FAIL for every headline.

Usage:
    python poc_meeting/audit_meeting_numbers.py
"""

import csv
import json
import math
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S47_ANALYSIS = os.path.join(BASE, "outputs/stage4_7/runs/run_array_20260610_1442/analysis")
S48_ANALYSIS = os.path.join(BASE, "outputs/stage4_8/runs/run_array_20260611_0109/analysis")
S48_REPRS = os.path.join(BASE, "outputs/stage4_8/runs/run_array_20260611_0109/representations")
FROZEN_MANIFEST = os.path.join(BASE, "outputs/stage4/token_dynamics/full_20260604_101929/manifest.json")
DIRECTION_PT = os.path.join(BASE, "outputs/stage4/qwen3-14b/refusal_direction/direction.pt")
OUT_DIR = os.path.join(BASE, "outputs/meeting/mahmood_20260611/audit")

os.makedirs(OUT_DIR, exist_ok=True)

results = []


def check(name, actual, expected, tol=0.02, direction=None):
    """Record a PASS/FAIL check. tol is relative tolerance for floats."""
    if isinstance(expected, float) and isinstance(actual, float):
        if expected == 0:
            ok = abs(actual - expected) < 0.001
        else:
            ok = abs(actual - expected) / abs(expected) <= tol
    elif isinstance(expected, bool):
        ok = (actual == expected)
    elif isinstance(expected, str):
        ok = (str(actual) == expected)
    else:
        ok = (actual == expected)
    status = "PASS" if ok else "FAIL"
    rec = {"check": name, "status": status, "actual": actual, "expected": expected}
    if direction:
        rec["direction"] = direction
    results.append(rec)
    symbol = "✓" if ok else "✗"
    print(f"  [{symbol}] {status:4s} | {name}: actual={actual}, expected={expected}")
    return ok


def check_exists(name, path):
    ok = os.path.exists(path)
    status = "PASS" if ok else "FAIL"
    symbol = "✓" if ok else "✗"
    results.append({"check": name, "status": status, "actual": ok, "expected": True})
    print(f"  [{symbol}] {status:4s} | {name}: {'exists' if ok else 'MISSING'} ({path})")
    return ok


def spearman(x, y):
    n = len(x)
    if n < 3:
        return float("nan")
    rx = sorted(range(n), key=lambda i: x[i])
    ry = sorted(range(n), key=lambda i: y[i])
    rankx = [0] * n
    ranky = [0] * n
    for rank, idx in enumerate(rx):
        rankx[idx] = rank + 1
    for rank, idx in enumerate(ry):
        ranky[idx] = rank + 1
    d2 = sum((rankx[i] - ranky[i]) ** 2 for i in range(n))
    return 1 - 6 * d2 / (n * (n**2 - 1))


def mean(lst):
    return sum(lst) / len(lst) if lst else float("nan")


# ── Stage 4 frozen artifacts ─────────────────────────────────────────────────
print("\n=== Stage 4 frozen artifacts ===")
check_exists("frozen_token_dynamics_manifest", FROZEN_MANIFEST)
check_exists("refusal_direction_pt", DIRECTION_PT)

if check_exists("frozen_manifest_readable", FROZEN_MANIFEST):
    with open(FROZEN_MANIFEST) as f:
        mf = json.load(f)
    # examples_attempted = total processed (completed + skipped via --resume)
    n_examples = mf.get("examples_attempted")
    check("stage4_n_examples_attempted_42", n_examples, 42)

# ── Stage 4 causal validation ─────────────────────────────────────────────────
print("\n=== Stage 4 causal validation ===")
intervention_file = os.path.join(
    BASE, "outputs/stage4/qwen3-14b/refusal_direction/intervention_selection_metrics.json"
)
if os.path.exists(intervention_file):
    with open(intervention_file) as f:
        interv = json.load(f)
    # Look for 0/160 survivors
    survivors = (
        interv.get("n_survivors")
        or interv.get("survivors")
        or interv.get("n_valid_interventions")
        or interv.get("total_survivors")
    )
    if survivors is not None:
        check("stage4a2_causal_survivors_0", survivors, 0)
    else:
        results.append({"check": "stage4a2_causal_survivors", "status": "SKIP",
                        "actual": "key_not_found", "expected": 0,
                        "note": str(list(interv.keys())[:10])})
        print("  [?] SKIP | stage4a2_causal_survivors: key not found in intervention_selection_metrics.json")

# ── Stage 4.7 ─────────────────────────────────────────────────────────────────
print("\n=== Stage 4.7 behavioral results ===")

# condition_summary.csv
cond_csv = os.path.join(S47_ANALYSIS, "condition_summary.csv")
check_exists("stage47_condition_summary_csv", cond_csv)

cond_data = {}
with open(cond_csv) as f:
    for row in csv.DictReader(f):
        cond_data[row["condition"]] = row

check("stage47_total_rows_48", sum(int(cond_data[c]["n"]) for c in cond_data), 48)
check("stage47_n_source_prompts_12", int(cond_data["A"]["n"]), 12)

# complete-case counts
check("stage47_A_n_censored_0", int(cond_data["A"]["n_censored"]), 0)
check("stage47_D_n_censored_1", int(cond_data["D"]["n_censored"]), 1)
check("stage47_F_n_censored_1", int(cond_data["F"]["n_censored"]), 1)
check("stage47_E_n_censored_3", int(cond_data["E"]["n_censored"]), 3)

check("stage47_A_cc_n_12", int(cond_data["A"]["n_complete_case"]), 12)
check("stage47_D_cc_n_11", int(cond_data["D"]["n_complete_case"]), 11)
check("stage47_F_cc_n_11", int(cond_data["F"]["n_complete_case"]), 11)
check("stage47_E_cc_n_9", int(cond_data["E"]["n_complete_case"]), 9)

check("stage47_A_cc_success_10", int(cond_data["A"]["n_cc_success"]), 10)
check("stage47_D_cc_success_5", int(cond_data["D"]["n_cc_success"]), 5)
check("stage47_F_cc_success_3", int(cond_data["F"]["n_cc_success"]), 3)
check("stage47_E_cc_success_4", int(cond_data["E"]["n_cc_success"]), 4)

check("stage47_A_cc_rate_0833", float(cond_data["A"]["cc_success_rate"]), 0.8333, tol=0.01)
check("stage47_D_cc_rate_0455", float(cond_data["D"]["cc_success_rate"]), 0.4545, tol=0.01)
check("stage47_F_cc_rate_0273", float(cond_data["F"]["cc_success_rate"]), 0.2727, tol=0.01)
check("stage47_E_cc_rate_0444", float(cond_data["E"]["cc_success_rate"]), 0.4444, tol=0.01)

# Note docs discrepancy
note_a = ("NOTE: some docs claim A=10/11 (91%) but artifact shows A=10/12 (83.3%, 0 censored). "
          "Corrective rerun eliminated A's censored row. Docs should be updated.")
results.append({"check": "stage47_A_rate_docs_discrepancy", "status": "INFO", "note": note_a})
print(f"  [i] INFO | stage47_A_rate_docs_discrepancy: {note_a}")

# thinking tokens
check("stage47_A_mean_think_11458", float(cond_data["A"]["mean_think_tokens"]), 11458.0, tol=0.005)
check("stage47_D_mean_think_2924", float(cond_data["D"]["mean_think_tokens"]), 2924.0, tol=0.005)
check("stage47_F_mean_think_824", float(cond_data["F"]["mean_think_tokens"]), 824.0, tol=0.01)

# ── Stage 4.7 sign tests ──────────────────────────────────────────────────────
print("\n=== Stage 4.7 sign tests ===")
sign_file = os.path.join(S47_ANALYSIS, "sign_tests.json")
check_exists("stage47_sign_tests_json", sign_file)
with open(sign_file) as f:
    sign = json.load(f)

check("stage47_AD_sign_p_0031", sign["A_vs_D"]["sign_test"]["p_two_sided"], 0.03125, tol=0.001)
check("stage47_AF_sign_p_0008", sign["A_vs_F"]["sign_test"]["p_two_sided"], 0.0078125, tol=0.001)
check("stage47_AF_mcnemar_p_0016", sign["A_vs_F"]["mcnemar"]["p_two_sided"], 0.015625, tol=0.001)
check("stage47_AE_sign_p_0031", sign["A_vs_E"]["sign_test"]["p_two_sided"], 0.03125, tol=0.001)

note_af = ("NOTE: A-F p reported as ~0.016 in docs = McNemar exact (0.01563). "
           "Sign test p = 0.00781. These are different tests.")
results.append({"check": "stage47_AF_pvalue_test_note", "status": "INFO", "note": note_af})
print(f"  [i] INFO | {note_af}")

# paired contrasts score diffs
pc_file = os.path.join(S47_ANALYSIS, "paired_contrasts.csv")
check_exists("stage47_paired_contrasts_csv", pc_file)
cont_diffs = {}
with open(pc_file) as f:
    for row in csv.DictReader(f):
        cont_diffs.setdefault(row["contrast"], []).append(float(row["score_diff_ref_minus_comp"]))

check("stage47_AD_score_diff_0417", mean(cont_diffs["A_vs_D"]), 0.4167, tol=0.01)
check("stage47_AF_score_diff_0583", mean(cont_diffs["A_vs_F"]), 0.5833, tol=0.01)
check("stage47_AE_score_diff_0490", mean(cont_diffs["A_vs_E"]), 0.4896, tol=0.01)

note_diffs = ("NOTE: some docs report A-D diff=0.438 and A-F diff=0.573. "
              "Artifacts show A-D=0.4167, A-F=0.5833 (all 12 pairs including legacy). "
              "Docs may have used an earlier or different analysis pass.")
results.append({"check": "stage47_score_diff_docs_discrepancy", "status": "INFO", "note": note_diffs})
print(f"  [i] INFO | {note_diffs}")

# think ratio
check("stage47_AF_think_ratio_1397", sign["A_vs_F"]["mean_think_ratio"], 13.97, tol=0.01)

# ── Stage 4.7 LOGO stability ──────────────────────────────────────────────────
print("\n=== Stage 4.7 LOGO stability ===")
logo_file = os.path.join(S47_ANALYSIS, "logo_sensitivity.json")
check_exists("stage47_logo_json", logo_file)
with open(logo_file) as f:
    logo = json.load(f)

check("stage47_AD_logo_always_positive", logo["stability"]["A_vs_D"]["always_positive"], True)
check("stage47_AF_logo_always_positive", logo["stability"]["A_vs_F"]["always_positive"], True)
check("stage47_AD_logo_n_folds_4", logo["stability"]["A_vs_D"]["n_folds"], 4)

# ── Stage 4.7 Layer-22 mechanistic ────────────────────────────────────────────
print("\n=== Stage 4.7 Layer-22 mechanistic ===")
mech_csv = os.path.join(S47_ANALYSIS, "mechanistic_summary.csv")
check_exists("stage47_mechanistic_summary_csv", mech_csv)

cond_l22 = {}
all_proj_A, all_log_think_A = [], []
with open(mech_csv) as f:
    for row in csv.DictReader(f):
        c = row["condition"]
        v_str = row.get("layer22_first_500_mean_projection", "")
        if v_str:
            cond_l22.setdefault(c, []).append(float(v_str))
        if c == "A":
            think_str = row.get("think_token_count", "")
            if think_str and float(think_str) > 0:
                all_proj_A.append(float(v_str))
                all_log_think_A.append(math.log(float(think_str)))

for c in ["A", "D", "F"]:
    if c in cond_l22:
        m = mean(cond_l22[c])
        cond_l22[c + "_mean"] = m

check("stage47_A_L22_first500_mean_727", cond_l22.get("A_mean", float("nan")), 7.26, tol=0.02)
check("stage47_D_L22_first500_mean_906", cond_l22.get("D_mean", float("nan")), 9.06, tol=0.02)
check("stage47_F_L22_first500_mean_850", cond_l22.get("F_mean", float("nan")), 8.50, tol=0.02)

# Mechanistic contrasts file
mc_file = os.path.join(S47_ANALYSIS, "mechanistic_contrasts.csv")
check_exists("stage47_mechanistic_contrasts_csv", mc_file)
ad_diff_l22 = None
spearman_rho_A = None
with open(mc_file) as f:
    for row in csv.DictReader(f):
        if row["layer"] == "22" and row["window"] == "first_500" and row["contrast"] == "A_vs_D":
            ad_diff_l22 = float(row["mean_diff"])
            spearman_rho_A = float(row.get("spearman_rho_vs_log_think_A", "nan"))

if ad_diff_l22 is not None:
    check("stage47_AD_L22_diff_neg179", ad_diff_l22, -1.793, tol=0.02)
if spearman_rho_A is not None:
    check("stage47_L22_spearman_rho_neg068", spearman_rho_A, -0.678, tol=0.03)

# Also compute Spearman for condition A from raw data
rho_A = spearman(all_proj_A, all_log_think_A)
check("stage47_L22_spearman_condA_neg068", rho_A, -0.678, tol=0.03)

# ── Stage 4.8 behavioral results ─────────────────────────────────────────────
print("\n=== Stage 4.8 behavioral results ===")
s48_cond_csv = os.path.join(S48_ANALYSIS, "condition_summary.csv")
check_exists("stage48_condition_summary_csv", s48_cond_csv)

s48_cond = {}
with open(s48_cond_csv) as f:
    for row in csv.DictReader(f):
        s48_cond[row["condition"]] = row

check("stage48_total_rows_60", sum(int(s48_cond[c]["n_total"]) for c in s48_cond), 60)
check("stage48_total_censored_0", sum(int(s48_cond[c]["n_censored"]) for c in s48_cond), 0)
check("stage48_A_success_12", int(s48_cond["A"]["n_success"]), 12)
check("stage48_D_success_10", int(s48_cond["D"]["n_success"]), 10)
check("stage48_F_success_8", int(s48_cond["F"]["n_success"]), 8)
check("stage48_A_rate_060", float(s48_cond["A"]["success_rate_complete"]), 0.60, tol=0.01)
check("stage48_D_rate_050", float(s48_cond["D"]["success_rate_complete"]), 0.50, tol=0.01)
check("stage48_F_rate_040", float(s48_cond["F"]["success_rate_complete"]), 0.40, tol=0.01)

# Stage 4.8 analysis summary
s48_summary_file = os.path.join(S48_ANALYSIS, "analysis_summary.json")
check_exists("stage48_analysis_summary_json", s48_summary_file)
with open(s48_summary_file) as f:
    s48_summary = json.load(f)

check("stage48_n_cells_12", s48_summary["n_cells"], 12)
check("stage48_matched_cells_3", s48_summary["n_matched_cells"], 3)

# Stage 4.8 variance decomposition
vd_file = os.path.join(S48_ANALYSIS, "variance_decomposition.json")
check_exists("stage48_variance_decomp_json", vd_file)
with open(vd_file) as f:
    vd = json.load(f)

check("stage48_within_cell_var_0053", vd["mean_within_cell_variance"], 0.0533, tol=0.03)
check("stage48_between_cell_var_0197", vd["between_cell_variance"], 0.1967, tol=0.03)
variance_ratio = vd["between_cell_variance"] / vd["mean_within_cell_variance"]
check("stage48_variance_ratio_369", variance_ratio, 3.69, tol=0.05)

# Stage 4.8 goal-level
s48_cell_csv = os.path.join(S48_ANALYSIS, "cell_summary.csv")
check_exists("stage48_cell_summary_csv", s48_cell_csv)
goal_success = {}
with open(s48_cell_csv) as f:
    for row in csv.DictReader(f):
        g = row["goal_index"]
        goal_success.setdefault(g, []).append(int(row["n_success"]))

goal1_total = sum(goal_success.get("1", []))
goal3_total = sum(goal_success.get("3", []))
check("stage48_goal1_total_success_0", goal1_total, 0)
check("stage48_goal3_total_success_15", goal3_total, 15)

# Stage 4.8 Layer-22 projections from representations
print("\n=== Stage 4.8 Layer-22 projections ===")
proj_file = os.path.join(S48_REPRS, "projection_summary.jsonl")
check_exists("stage48_projection_summary_jsonl", proj_file)

s48_l22 = {}
with open(proj_file) as f:
    for line in f:
        row = json.loads(line)
        c = row["condition"]
        v = row.get("layer22_first_500_mean_projection")
        if v is not None:
            s48_l22.setdefault(c, []).append(v)

check("stage48_A_L22_mean_712", mean(s48_l22.get("A", [])), 7.12, tol=0.02)
check("stage48_F_L22_mean_808", mean(s48_l22.get("F", [])), 8.08, tol=0.02)
check("stage48_D_L22_mean_895", mean(s48_l22.get("D", [])), 8.95, tol=0.02)

# Verify ordering A < F < D (mechanistic null)
a_m = mean(s48_l22.get("A", []))
f_m = mean(s48_l22.get("F", []))
d_m = mean(s48_l22.get("D", []))
check("stage48_L22_ordering_A_lt_F", a_m < f_m, True,
      direction="A < F < D (opposite behavioral ordering A > D > F)")
check("stage48_L22_ordering_F_lt_D", f_m < d_m, True)

# ── Output ─────────────────────────────────────────────────────────────────────
pass_count = sum(1 for r in results if r["status"] == "PASS")
fail_count = sum(1 for r in results if r["status"] == "FAIL")
skip_count = sum(1 for r in results if r["status"] == "SKIP")
info_count = sum(1 for r in results if r["status"] == "INFO")

print(f"\n{'='*60}")
print(f"AUDIT SUMMARY: {pass_count} PASS / {fail_count} FAIL / {skip_count} SKIP / {info_count} INFO")
print(f"{'='*60}")

# Write JSON
json_path = os.path.join(OUT_DIR, "meeting_numbers_audit.json")
with open(json_path, "w") as f:
    json.dump({"summary": {"pass": pass_count, "fail": fail_count,
                           "skip": skip_count, "info": info_count},
               "checks": results}, f, indent=2)

# Write Markdown report
md_path = os.path.join(OUT_DIR, "meeting_numbers_audit.md")
with open(md_path, "w") as f:
    f.write("# Meeting Numbers Audit Report\n\n")
    f.write(f"**Date:** 2026-06-11  \n")
    f.write(f"**Summary:** {pass_count} PASS / {fail_count} FAIL / {skip_count} SKIP / {info_count} INFO\n\n")
    f.write("## Checks\n\n")
    f.write("| Status | Check | Actual | Expected |\n")
    f.write("|--------|-------|--------|----------|\n")
    for r in results:
        note = r.get("note", "")
        expected = r.get("expected", "")
        actual = r.get("actual", "")
        direction = r.get("direction", "")
        if note:
            f.write(f"| {r['status']} | {r['check']} | — | — |\n")
            f.write(f"| | *{note}* | | |\n")
        else:
            extra = f" ({direction})" if direction else ""
            f.write(f"| {r['status']} | {r['check']}{extra} | `{actual}` | `{expected}` |\n")
    f.write("\n## Key Findings\n\n")
    f.write("### Stage 4.7 Complete-Case Counts\n\n")
    f.write("| Condition | n_censored | n_complete_case | n_cc_success | cc_rate |\n")
    f.write("|-----------|-----------|----------------|-------------|--------|\n")
    for c in ["A", "D", "F", "E"]:
        row = cond_data.get(c, {})
        f.write(f"| {c} | {row.get('n_censored','')} | {row.get('n_complete_case','')} | "
                f"{row.get('n_cc_success','')} | {float(row.get('cc_success_rate',0)):.1%} |\n")
    f.write("\n**Docs discrepancy**: Multiple docs claim A=10/11 (91%). Artifact shows A=10/12 (83.3%, 0 censored).\n\n")
    f.write("### Stage 4.8 Results\n\n")
    f.write("| Condition | n_total | n_success | success_rate |\n")
    f.write("|-----------|---------|-----------|-------------|\n")
    for c in ["A", "D", "F"]:
        row = s48_cond.get(c, {})
        f.write(f"| {c} | {row.get('n_total','')} | {row.get('n_success','')} | "
                f"{float(row.get('success_rate_complete',0)):.0%} |\n")
    f.write(f"\nVariance ratio (between/within): {variance_ratio:.2f}×\n\n")
    f.write("### Layer-22 First-500 Mean Projection\n\n")
    f.write("| Stage | A | F | D | Ordering |\n")
    f.write("|-------|---|---|---|----------|\n")
    a47 = mean(cond_l22.get("A", [])); f47 = mean(cond_l22.get("F", [])); d47 = mean(cond_l22.get("D", []))
    f.write(f"| 4.7 | {a47:.3f} | {f47:.3f} | {d47:.3f} | A < F < D (opposite behavioral) |\n")
    f.write(f"| 4.8 | {a_m:.3f} | {f_m:.3f} | {d_m:.3f} | A < F < D (replicated) |\n")

# Write verified_headline_numbers.csv
csv_path = os.path.join(OUT_DIR, "verified_headline_numbers.csv")
headlines = [
    ("stage", "metric", "value", "unit", "source"),
    ("4.7", "n_total_rows", "48", "rows", "condition_summary.csv"),
    ("4.7", "n_source_prompts", "12", "prompts", "condition_summary.csv"),
    ("4.7", "A_n_censored", "0", "rows", "condition_summary.csv"),
    ("4.7", "D_n_censored", "1", "rows", "condition_summary.csv"),
    ("4.7", "F_n_censored", "1", "rows", "condition_summary.csv"),
    ("4.7", "E_n_censored", "3", "rows", "condition_summary.csv"),
    ("4.7", "A_cc_success", "10/12", "fraction", "condition_summary.csv"),
    ("4.7", "D_cc_success", "5/11", "fraction", "condition_summary.csv"),
    ("4.7", "F_cc_success", "3/11", "fraction", "condition_summary.csv"),
    ("4.7", "E_cc_success", "4/9", "fraction", "condition_summary.csv"),
    ("4.7", "A_cc_rate", "0.833", "rate", "condition_summary.csv"),
    ("4.7", "D_cc_rate", "0.455", "rate", "condition_summary.csv"),
    ("4.7", "F_cc_rate", "0.273", "rate", "condition_summary.csv"),
    ("4.7", "E_cc_rate", "0.444", "rate", "condition_summary.csv"),
    ("4.7", "A_mean_think_tokens", "11458", "tokens", "condition_summary.csv"),
    ("4.7", "D_mean_think_tokens", "2924", "tokens", "condition_summary.csv"),
    ("4.7", "F_mean_think_tokens", "824", "tokens", "condition_summary.csv"),
    ("4.7", "AF_think_ratio", "13.97", "ratio", "sign_tests.json"),
    ("4.7", "AD_sign_test_p", "0.03125", "p-value", "sign_tests.json"),
    ("4.7", "AF_sign_test_p", "0.00781", "p-value", "sign_tests.json"),
    ("4.7", "AF_mcnemar_p", "0.01563", "p-value", "sign_tests.json"),
    ("4.7", "AE_sign_test_p", "0.03125", "p-value", "sign_tests.json"),
    ("4.7", "AD_score_diff", "0.4167", "difference", "paired_contrasts.csv"),
    ("4.7", "AF_score_diff", "0.5833", "difference", "paired_contrasts.csv"),
    ("4.7", "AE_score_diff", "0.4896", "difference", "paired_contrasts.csv"),
    ("4.7", "AD_LOGO_always_positive", "True", "bool", "logo_sensitivity.json"),
    ("4.7", "AF_LOGO_always_positive", "True", "bool", "logo_sensitivity.json"),
    ("4.7", "A_L22_first500_mean", f"{mean(cond_l22.get('A',[])):.3f}", "projection", "mechanistic_summary.csv"),
    ("4.7", "D_L22_first500_mean", f"{mean(cond_l22.get('D',[])):.3f}", "projection", "mechanistic_summary.csv"),
    ("4.7", "F_L22_first500_mean", f"{mean(cond_l22.get('F',[])):.3f}", "projection", "mechanistic_summary.csv"),
    ("4.7", "AD_L22_first500_diff", f"{ad_diff_l22:.4f}" if ad_diff_l22 else "N/A", "difference", "mechanistic_contrasts.csv"),
    ("4.7", "L22_spearman_rho_vs_log_think_condA", f"{spearman_rho_A:.4f}" if spearman_rho_A else "N/A", "rho", "mechanistic_contrasts.csv"),
    ("4.8", "n_total_rows", "60", "rows", "condition_summary.csv"),
    ("4.8", "n_censored", "0", "rows", "condition_summary.csv"),
    ("4.8", "A_success", "12/20", "fraction", "condition_summary.csv"),
    ("4.8", "D_success", "10/20", "fraction", "condition_summary.csv"),
    ("4.8", "F_success", "8/20", "fraction", "condition_summary.csv"),
    ("4.8", "A_rate", "0.60", "rate", "condition_summary.csv"),
    ("4.8", "D_rate", "0.50", "rate", "condition_summary.csv"),
    ("4.8", "F_rate", "0.40", "rate", "condition_summary.csv"),
    ("4.8", "n_cells", "12", "cells", "analysis_summary.json"),
    ("4.8", "n_matched_cells", "3", "cells", "analysis_summary.json"),
    ("4.8", "within_cell_variance", "0.0533", "variance", "variance_decomposition.json"),
    ("4.8", "between_cell_variance", "0.1967", "variance", "variance_decomposition.json"),
    ("4.8", "variance_ratio", f"{variance_ratio:.2f}", "ratio", "variance_decomposition.json"),
    ("4.8", "goal1_total_success", "0/15", "fraction", "cell_summary.csv"),
    ("4.8", "goal3_total_success", "15/15", "fraction", "cell_summary.csv"),
    ("4.8", "A_L22_first500_mean", f"{mean(s48_l22.get('A',[])):.3f}", "projection", "projection_summary.jsonl"),
    ("4.8", "D_L22_first500_mean", f"{mean(s48_l22.get('D',[])):.3f}", "projection", "projection_summary.jsonl"),
    ("4.8", "F_L22_first500_mean", f"{mean(s48_l22.get('F',[])):.3f}", "projection", "projection_summary.jsonl"),
]
with open(csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(headlines)

print(f"\nOutputs written to: {OUT_DIR}")
print(f"  {json_path}")
print(f"  {md_path}")
print(f"  {csv_path}")

if fail_count > 0:
    print(f"\nWARNING: {fail_count} checks FAILED — review before presenting to Mahmood.")
    sys.exit(1)
else:
    print(f"\nAll checks PASSED (plus {info_count} informational notes).")
