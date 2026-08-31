#!/usr/bin/env python
"""RAH3 reproduction manifest -- and it EXECUTES.

⚠ A manifest that has never been run is a hypothesis (§58). This one recomputes every headline
number from the raw artifacts and compares against the value the reports publish. It writes
reports/RAH3_REPRO_MANIFEST.json with a PASS/FAIL per headline.

⚠ Fail-closed globbing. `rah_repro_manifest.newest()` returns the LAST glob hit, so a new run under
a matching prefix silently redefines what a published headline points at. `one()` refuses instead.

⚠ RELATIVE tolerance. Absolute tolerance is vacuous against 1e-08 values (`RAH2-C-023`).
"""
import glob
import hashlib
import json
import os
import subprocess
import sys

REL = 1e-6
RESULTS = []


def one(pattern):
    hits = sorted(glob.glob(pattern))
    if len(hits) != 1:
        raise SystemExit("expected exactly 1 file for %r, found %d: %r" % (pattern, len(hits), hits))
    return hits[0]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def record(headline, expected, got, artifact, command, note=""):
    if isinstance(expected, (int, float)) and isinstance(got, (int, float)):
        ok = abs(got - expected) <= REL * abs(expected) + 1e-300
    else:
        ok = got == expected
    RESULTS.append({"headline": headline, "expected": expected, "recomputed": got, "pass": bool(ok),
                    "artifact": artifact, "artifact_sha256": sha(artifact) if artifact else None,
                    "command": command, "note": note})
    print("  %-64s %s  (expected %r, got %r)" % (headline, "PASS" if ok else "FAIL", expected, got))
    return ok


def best(art, form):
    return max([c for c in art["grid"] if c["form"] == form], key=lambda c: c["pos_ctrl_max"])


def main():
    P_NEW = one("outputs/boombness/rah_preflight/rah3nc_p_cb_*.json")
    Q_NEW = one("outputs/boombness/rah_preflight/rah3nc_q_cb_*.json")
    P_OLD = one("outputs/boombness/rah_preflight/rah2pcf_p_cb_*.json")
    Q_OLD = one("outputs/boombness/rah_preflight/rah2pcf_q_cb_*.json")
    PROBE = one("outputs/boombness/rah_preflight/rah3_capture_site_probe.json")
    FROZEN = one("reports/RAH3_FROZEN_CONFIG.json")
    pn, qn, po, qo = (json.load(open(p)) for p in (P_NEW, Q_NEW, P_OLD, Q_OLD))
    probe, frozen = json.load(open(PROBE)), json.load(open(FROZEN))

    RUN = ("sbatch --export=ALL,BOOMB_SCRIPT=rah_preflight_transport.py,"
           "BOOMB_ARGSFILE=$PWD/runargs/rah3/%s.txt src/boombness/slurm/run_boombness.sh")

    print("\n[A] the capture site is non-copy on every row")
    record("capture piece is '.' on all 8 Llama donors", 1,
           len({d["donor_piece"] for d in pn["donors"]}), P_NEW, RUN % "nc_p_cb")
    record("capture piece value (Llama)", ".", pn["donors"][0]["donor_piece"], P_NEW, RUN % "nc_p_cb")
    record("capture piece is '.' on all 8 Qwen3 donors", 1,
           len({d["donor_piece"] for d in qn["donors"]}), Q_NEW, RUN % "nc_q_cb")
    for art, path, tag in ((pn, P_NEW, "Llama"), (qn, Q_NEW, "Qwen3")):
        record("%s: 0 donors overlap the concept surface" % tag, 0,
               sum(1 for d in art["donors"] if d["overlaps_concept_surface"]), path, RUN)
        record("%s: 0 donors overlap the codeword surface" % tag, 0,
               sum(1 for d in art["donors"] if d["overlaps_codeword_surface"]), path, RUN)
        record("%s: 0 donors are a candidate label" % tag, 0,
               sum(1 for d in art["donors"] if d["is_candidate_label"]), path, RUN)
        record("%s: capture_offset is the registered +1" % tag, 1, art["capture_offset"], path, RUN)
    record("probe: offset 0 disqualified on 8/8 rows, all 4 cells", 4,
           sum(1 for k, v in probe.items()
               if all(r["off0"]["overlaps_concept"] for r in v["rows"]) and len(v["rows"]) == 8),
           PROBE, "python scripts/rah3_capture_site_probe.py <out>")

    print("\n[B] the collapse, offset 0 -> offset +1")
    for tag, old, new, path in (("Llama", po, pn, P_NEW), ("Qwen3", qo, qn, Q_NEW)):
        for form, want in ((("id07_raw", 687.5), ("id07_tmpl", 42808.9), ("fc_probe_last", 4.7),
                            ("fewshot_cat", 650.9), ("fewshot_syn", 153.2)) if tag == "Llama" else
                           (("id07_raw", 8062.3), ("id07_tmpl", 140.5), ("fc_probe_last", 1855.3),
                            ("fewshot_cat", 97.3), ("fewshot_syn", 460.6))):
            r = best(old, form)["pos_ctrl_max"] / best(new, form)["pos_ctrl_max"]
            RESULTS.append({"headline": "%s %s collapse factor" % (tag, form),
                            "expected": want, "recomputed": round(r, 1),
                            "pass": abs(round(r, 1) - want) <= 0.15,
                            "artifact": path, "artifact_sha256": sha(path), "command": RUN})
            print("  %-64s %s  (expected %r, got %r)"
                  % ("%s %s collapse factor" % (tag, form),
                     "PASS" if abs(round(r, 1) - want) <= 0.15 else "FAIL", want, round(r, 1)))

    print("\n[C] the verdicts")
    record("Llama verdict", "P-B",
           frozen["models"]["meta-llama/Llama-3.1-8B-Instruct"]["verdict"], FROZEN,
           "python scripts/rah3_select_config.py --dev ... --dev ...")
    record("Qwen3 verdict", "P-D", frozen["models"]["Qwen/Qwen3-14B"]["verdict"], FROZEN,
           "python scripts/rah3_select_config.py --dev ... --dev ...")
    record("held_out_may_run", False, frozen["held_out_may_run"], FROZEN, "same")
    for tag, art, path in (("Llama", pn, P_NEW), ("Qwen3", qn, Q_NEW)):
        record("%s: eligible cells" % tag, 10, art["RAH3"]["n_eligible_cells"], path, RUN)
        record("%s: eligible AND passing" % tag, 0, art["RAH3"]["n_eligible_and_passing"], path, RUN)
        record("%s: vacuous-patch cells" % tag, 0, art["RAH3"]["n_vacuous_patch_cells"], path, RUN)

    print("\n[D] the frozen cell (the only cell the P-B verdict rests on)")
    fc = best(pn, "fc_probe_last")
    record("Llama fc_probe_last p_concept", 0.193181, round(fc["pos_ctrl_max"], 6), P_NEW, RUN)
    record("Llama fc_probe_last p_codeword", 0.002296, round(fc["p_codeword_at_best"], 6), P_NEW, RUN)
    record("Llama fc_probe_last option mass", 0.745978,
           round(fc["patched_option_mass_at_best"], 6), P_NEW, RUN)
    record("Llama fc_probe_last R", 4, fc["R"], P_NEW, RUN)
    record("Llama fc_probe_last donor L", 11, fc["best_donor_L"], P_NEW, RUN)
    record("Llama fc_probe_last hops", 8, fc["hops"], P_NEW, RUN)
    record("fc_probe_last is NOT exposure-clean", 4, len(fc["names_candidates"]), P_NEW, RUN)
    be = max([c for c in pn["grid"] if c["rah3_eligible"]], key=lambda c: c["pos_ctrl_max"])
    record("Llama best ELIGIBLE cell option mass", 0.000133,
           round(be["patched_option_mass_at_best"], 6), P_NEW, RUN)
    record("  ... x below MASS_GATE", 376,
           round(pn["MASS_GATE"] / be["patched_option_mass_at_best"]), P_NEW, RUN)
    record("Qwen3 best cell over ALL forms", 0.000539,
           round(max(c["pos_ctrl_max"] for c in qn["grid"]), 6), Q_NEW, RUN)
    # ⚠ `RAH3-C-012`. This manifest caught my OWN overstatement: the reports said "1.000", a
    # ROUNDED value presented as exact. The true value is 0.999999. The 1855x collapse is
    # unaffected -- it was computed from the true value -- but "1.000" is not what the artifact says.
    record("Qwen3 offset-0 fc_probe_last (NOT 1.000 -- rounded)", 0.999999,
           round(best(qo, "fc_probe_last")["pos_ctrl_max"], 6), Q_OLD,
           RUN % "(rah2pcf, prior phase)")

    print("\n[E] gates are LIVE, not decorative")
    record("MASS_GATE persisted", 0.05, pn["MASS_GATE"], P_NEW, RUN)
    record("TRANSPORT_POSITIVE_CONTROL_THRESHOLD persisted", 0.1,
           pn["TRANSPORT_POSITIVE_CONTROL_THRESHOLD"], P_NEW, RUN)
    record("held-out artifacts do NOT exist (gated off)", 0,
           len(glob.glob("outputs/boombness/rah_preflight/rah3nc_*_lp_*.json")), None,
           "ls outputs/boombness/rah_preflight/rah3nc_*_lp_*.json")

    print("\n[F] provenance")
    for tag, art, path in (("Llama", pn, P_NEW), ("Qwen3", qn, Q_NEW)):
        p = art.get("provenance", {})
        miss = [f for f in ("git_commit", "git_dirty", "branch", "hostname", "argv",
                            "python_executable", "bank_sha256", "expected_n_donors",
                            "actual_n_donors", "slurm_job_id") if f not in p]
        record("%s: provenance complete" % tag, [], miss, path, RUN)
        record("%s: bank sha matches disk" % tag, sha(art["bank"]), p.get("bank_sha256"), path, RUN)

    npass = sum(1 for r in RESULTS if r["pass"])
    out = {"schema": "RAH3_REPRO_MANIFEST/1",
           "executed": True,
           "git_commit": subprocess.run(("git", "rev-parse", "HEAD"), capture_output=True,
                                        text=True).stdout.strip(),
           "git_dirty": bool(subprocess.run(("git", "status", "--porcelain"), capture_output=True,
                                            text=True).stdout.strip()),
           "n_headlines": len(RESULTS), "n_pass": npass, "n_fail": len(RESULTS) - npass,
           "tolerance": "relative %g (absolute tolerance is vacuous against 1e-08 values)" % REL,
           "headlines": RESULTS}
    os.makedirs("reports", exist_ok=True)
    with open("reports/RAH3_REPRO_MANIFEST.json", "w") as fh:
        json.dump(out, fh, indent=1)
    print("\n%d headlines, %d PASS, %d FAIL -> reports/RAH3_REPRO_MANIFEST.json"
          % (len(RESULTS), npass, len(RESULTS) - npass))
    for r in RESULTS:
        if not r["pass"]:
            print("  FAIL: %s expected=%r got=%r" % (r["headline"], r["expected"], r["recomputed"]))
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
