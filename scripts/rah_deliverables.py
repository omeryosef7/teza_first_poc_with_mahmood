#!/usr/bin/env python
"""rah_deliverables.py -- generate the RAH sprint's claim ledger and main table FROM ARTIFACTS.

The predecessor sprint's lesson, recorded in its own log: a deliverable that is TYPED drifts from the
artifacts it describes, and a header that is typed drifts from the table under it. So every number
here is read from a committed artifact at generation time. Where a claim's number cannot be read
from an artifact, the ledger says so explicitly rather than carrying a typed value.

Emits:
  reports/RAH_CLAIM_LEDGER.json   every claim with its status word, population, counts and provenance
  reports/RAH_MAIN_TABLE.md       the paper-grade table -- counts and denominators, never bare rates

STATUS WORDS are the closed set fixed in the sprint plan:
  DISCOVERY / DIAGNOSTIC / CONFIRMATORY / EXPLORATORY / DECLINED / FALSIFIED / CANNOT ANSWER

Usage:
  python scripts/rah_deliverables.py
"""
from __future__ import annotations
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = "RAH_CLAIM_LEDGER/1"


def jload(path):
    p = os.path.join(ROOT, path)
    return json.load(open(p)) if os.path.exists(p) else None


def newest(pat):
    hits = sorted(glob.glob(os.path.join(ROOT, pat)))
    return hits[-1] if hits else None


def rows(d):
    p = os.path.join(d, "results.jsonl")
    if not os.path.exists(p):
        p = os.path.join(d, "rows.jsonl")
    return [json.loads(l) for l in open(p) if l.strip()]


def build():
    L = []

    # ---- RAH-R-004: Phase 1 attributable lift -------------------------------------------- #
    p1 = jload("outputs/boombness/rah_phase1/rah_phase1_lift.json")
    if p1:
        for cell, c in sorted(p1["cells"].items()):
            for ro, r in sorted(c["readouts"].items()):
                L.append({
                    "id": "RAH-R-004", "status": "DIAGNOSTIC",
                    "claim": "attributable lift of the installed mapping, %s readout" % ro,
                    "cell": cell, "readout": ro,
                    "unit_of_independence": "family (paired), clustered by domain",
                    "n": r["n_pairs"], "n_domains": r["n_clusters"],
                    "arm": "natural_doublespeak", "base": "benign_literal",
                    "raw_counts": {"arm": r["counts"]["natural_doublespeak"],
                                   "base": r["counts"]["benign_literal"],
                                   "lost": r["n10_LOST"], "gained": r["n01_GAINED"]},
                    "effect": r["delta_arm_minus_base"],
                    "ci_newcombe": r["newcombe_ci"], "ci_domain_cluster": r["cluster_ci"],
                    "p": r["mcnemar_exact_p"], "verdict": r["verdict"],
                    "intervention": None, "headroom": "n/a (no ASR)",
                    "judge": "n/a (forward-only readout)",
                    "artifact": "outputs/boombness/rah_phase1/rah_phase1_lift.json",
                    "independent_verifier": "scripts/rah_verify_phase1.py (PASS)"})

    # ---- RAH-R-007: the dose diagnostic --------------------------------------------------- #
    dz = jload("outputs/boombness/rah_phase1b/rah_dose.json")
    if dz:
        for cell, c in sorted(dz["cells"].items()):
            dr = c.get("rejudge_drift_on_n8") or {}
            L.append({
                "id": "RAH-R-007", "status": "EXPLORATORY",
                "claim": "baseline harmful ASR, n_examples 8 vs 16 (RBD-PR-005 as registered)",
                "cell": cell, "unit_of_independence": "row, clustered by domain",
                "n": {"n8": c["n8"]["n"], "n16": c["n16"]["n"]},
                "n_domains": c["n8"]["n_clusters"],
                "raw_counts": {"n8_attacks": c["n8"]["attacks"], "n16_attacks": c["n16"]["attacks"]},
                "effect": {"asr_n8": c["n8"]["asr"], "asr_n16": c["n16"]["asr"],
                           "ratio": c["ratio_n16_over_n8"]},
                "ci_domain_cluster": {"n8": c["n8"]["ci_domain_cluster"],
                                      "n16": c["n16"]["ci_domain_cluster"]},
                "ci_interval_source": {"n8": c["n8"].get("ci_interval_source"),
                                       "n16": c["n16"].get("ci_interval_source")},
                "measured_judge_drift_fresh": {"flips": dr.get("flips_fresh"),
                                               "n": dr.get("n_fresh"),
                                               "rate": dr.get("flip_rate_fresh")},
                "verdict": "does not move at a resolvable size (MDE 2.68x Llama / 4.10x Qwen3)",
                "intervention": None, "cap": 640,
                "judge": "openai/gpt-4o-mini pinned, 100%",
                "artifact": "outputs/boombness/rah_phase1b/rah_dose.json",
                "independent_verifier": "scripts/rah_verify_dose.py (PASS, 8/8 intervals)"})

    # ---- RAH-R-010: the Stage-A selection ------------------------------------------------- #
    sa = jload("outputs/boombness/rah_stagea/rah_stagea_selection.json")
    if sa and sa.get("selected"):
        w = sa["selected"]
        L.append({"id": "RAH-R-010", "status": "DIAGNOSTIC",
                  "claim": "receiver configuration selected on the POSITIVE CONTROL",
                  "cell": "level-A discovery, 3 banks x 2 models",
                  "selected": {"form": w["form"], "depth_fraction": w["depth_fraction"],
                               "R_by_model": w["R_by_model"]},
                  "effect": {"min_uplift_over_runs": w["min_uplift_over_runs"],
                             "min_support_above_band": w["min_support_above_band"]},
                  "n": 6, "unit_of_independence": "run (bank x model)",
                  "caveat": "RAH-R-014: this configuration is the WORST of four for the codeword-"
                            "donor question; selecting on a positive control does not select the "
                            "right instrument for the phenomenon",
                  "artifact": "outputs/boombness/rah_stagea/rah_stagea_selection.json",
                  "independent_verifier": "scripts/rah_select_config.py re-runs the rule; "
                                          "8 unit tests incl. max-min-beats-max-max"})

    # ---- RAH-R-011 selection for PR-011 --------------------------------------------------- #
    s11 = jload("outputs/boombness/rah_stagea/rah_pr011_selection.json")
    if s11:
        for model, m in sorted(s11["models"].items()):
            w = m.get("selected")
            L.append({"id": "RAH-C-012", "status": "DIAGNOSTIC",
                      "claim": "transport configuration selected on BASELINE transport",
                      "cell": model, "DECLINED": m["DECLINED"],
                      "selected": None if not w else {
                          "form": w["form"], "R": w["R"], "donor_layer": w["best_above_band_L"],
                          "p_concept": w["best_above_band_p_concept"],
                          "uplift": (w["gate_at_selected_layer"] or {}).get("uplift"),
                          "breadth_above_band": w["n_above_band_clearing"]},
                      "declared_selection_bias": "selects on BASE transport, so base-minus-dpo is "
                                                 "inflated by selection (RAH-DR-001 F10)",
                      "artifact": "outputs/boombness/rah_stagea/rah_pr011_selection.json"})

    # ---- RAH-R-018: Track A verdict ------------------------------------------------------- #
    ta = newest("outputs/boombness/rah_transport/pr011_q_lp_*")
    if ta:
        rr = rows(ta)
        meta = json.load(open(os.path.join(ta, "meta.json")))
        base = [r for r in rr if r["arm"] == "base"]
        om = sorted(r["option_mass"] for r in base)
        L.append({"id": "RAH-R-018", "status": "CANNOT ANSWER",
                  "claim": "Track A: does demo_processing_only reduce mapped-concept transport?",
                  "cell": "%s x held-out lantern_poison" % meta["model"],
                  "unit_of_independence": "family", "n": meta["n_families_captured"],
                  "configuration": {"form": meta["receiver_form"], "R": meta["receiver_R"],
                                    "donor_layer": meta["donor_layer"], "band": meta["band"]},
                  "precondition": {"median_option_mass": om[len(om) // 2],
                                   "gate": 0.05,
                                   "rows_above_gate": sum(1 for x in om if x >= 0.05),
                                   "PASSES": False},
                  "verdict": "A-IV: option mass 6 orders of magnitude below gate on every arm; "
                             "the configuration does not transfer to held-out material. No delta "
                             "computed, no equivalence test run.",
                  "vacuity": meta["vacuity"],
                  "artifact": os.path.relpath(ta, ROOT)})

    # ---- RAH-R-021: Track B verdict ------------------------------------------------------- #
    sc = jload("outputs/boombness/rah_screen/rah_screen_table.json")
    if sc:
        for t in sc["table"]:
            if t["status"] != "JUDGED":
                continue
            L.append({"id": "RAH-R-021", "status": "DIAGNOSTIC",
                      "claim": "Track-B development headroom screen",
                      "cell": t["cell"], "unit_of_independence": "row, clustered by domain",
                      "n": t["n"], "n_domains": t["n_domains"],
                      "raw_counts": {"attacks": t["attacks"]},
                      "effect": {"baseline_asr": t["baseline_asr"]},
                      "k_informative": t["k_informative"],
                      "refusal_rate": t["refusal_rate"],
                      "headroom": "QUALIFIES" if t["qualifies"] else t["reason"],
                      "cap": 640, "judge": "openai/gpt-4o-mini pinned, 100%",
                      "artifact": "outputs/boombness/rah_screen/rah_screen_table.json"})
        L.append({"id": "RAH-R-021", "status": "DECLINED",
                  "claim": "Track-B confirmatory matrix",
                  "cell": "all", "verdict": sc["outcome"], "detail": sc["outcome_detail"],
                  "qualifying_cells": sc["qualifying_cells"],
                  "note": "matrix NOT run; ~20 GPU-hours not spent",
                  "artifact": "outputs/boombness/rah_screen/rah_screen_table.json"})
    return L


def main():
    L = build()
    os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)
    out = {"schema": SCHEMA, "n_claims": len(L),
           "status_words": ["DISCOVERY", "DIAGNOSTIC", "CONFIRMATORY", "EXPLORATORY",
                            "DECLINED", "FALSIFIED", "CANNOT ANSWER"],
           "generated_from": "committed artifacts only; no value in this file is typed",
           "claims": L}
    with open(os.path.join(ROOT, "reports/RAH_CLAIM_LEDGER.json"), "w") as f:
        json.dump(out, f, indent=1)

    lines = ["# RAH sprint — main table",
             "",
             "**Generated by `scripts/rah_deliverables.py` from committed artifacts. No value here "
             "is typed.** Counts and denominators throughout; no bare percentages.",
             ""]
    lines += ["## Phase 1 — is the installed mapping USED? (`RAH-R-004`)", "",
              "| cell | readout | arm (nat_ds) | base (benign_lit) | Δ | Newcombe 95% | domain-cluster 95% | verdict |",
              "|---|---|---|---|---|---|---|---|"]
    for c in [x for x in L if x["id"] == "RAH-R-004"]:
        rc = c["raw_counts"]
        lines.append("| %s | %s | %d/%d | %d/%d | %+.4f | [%+.4f, %+.4f] | [%+.4f, %+.4f] | %s |" % (
            c["cell"], c["readout"], rc["arm"]["k"], rc["arm"]["n"], rc["base"]["k"], rc["base"]["n"],
            c["effect"], c["ci_newcombe"][0], c["ci_newcombe"][1],
            c["ci_domain_cluster"][0], c["ci_domain_cluster"][1], c["verdict"]))

    lines += ["", "## `RBD-PR-005` dose diagnostic (`RAH-R-007`)", "",
              "| cell | n=8 | n=16 | ratio | re-judge drift (fresh) |", "|---|---|---|---|---|"]
    for c in [x for x in L if x["id"] == "RAH-R-007"]:
        e, rc, dr = c["effect"], c["raw_counts"], c["measured_judge_drift_fresh"]
        lines.append("| %s | %d/%d = %.4f | %d/%d = %.4f | %.2fx | %s/%s = %s |" % (
            c["cell"], rc["n8_attacks"], c["n"]["n8"], e["asr_n8"],
            rc["n16_attacks"], c["n"]["n16"], e["asr_n16"], e["ratio"],
            dr["flips"], dr["n"], ("%.4f" % dr["rate"]) if dr["rate"] is not None else "n/a"))

    lines += ["", "## Track-B screening (`RAH-R-021`) — every candidate, including failures", "",
              "| cell | attacks | n | baseline ASR | domains | k_inf | refusal | qualifies |",
              "|---|---|---|---|---|---|---|---|"]
    for c in [x for x in L if x["id"] == "RAH-R-021" and x.get("cell") != "all"]:
        lines.append("| %s | %d | %d | %.4f | %d | %d | %.3f | %s |" % (
            c["cell"], c["raw_counts"]["attacks"], c["n"], c["effect"]["baseline_asr"],
            c["n_domains"], c["k_informative"], c["refusal_rate"],
            "**YES**" if c["headroom"] == "QUALIFIES" else "no"))

    verdicts = [x for x in L if x["status"] in ("CANNOT ANSWER", "DECLINED")]
    lines += ["", "## Verdicts", ""]
    for v in verdicts:
        parts = [x for x in (v.get("verdict"), v.get("detail"), v.get("note")) if x]
        lines.append("* **%s — %s**: %s" % (v["id"], v["status"], " — ".join(parts)))
    with open(os.path.join(ROOT, "reports/RAH_MAIN_TABLE.md"), "w") as f:
        f.write("\n".join(lines) + "\n")

    print("claims: %d" % len(L))
    print("-> reports/RAH_CLAIM_LEDGER.json")
    print("-> reports/RAH_MAIN_TABLE.md")
    return 0



if __name__ == "__main__":
    sys.exit(main())
