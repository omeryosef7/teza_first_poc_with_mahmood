#!/usr/bin/env python
"""rah_repro_manifest.py -- the RAH reproduction manifest, and it EXECUTES.

§12.6 requires that for every paper-level number the sprint records the raw artifact, the producing
command, an independent verifier and the commit -- and that the manifest be **actually executed**
before sprint close. A manifest that is only a list is a promise; this one runs.

For each entry it:
  1. checks the raw artifact exists,
  2. RUNS the independent verifier (a program that does not import the producer),
  3. re-reads the headline number from the artifact and compares it to the value recorded here,
  4. reports PASS/FAIL per entry and refuses to exit 0 if any entry fails.

The recorded values below are the ONLY typed numbers in the sprint's deliverables, and they exist
precisely so that a silent change in an artifact is caught: if a number here stops matching its
artifact, that is a FAILURE, not a value to update.

Usage:
  python scripts/rah_repro_manifest.py [--out reports/RAH_REPRO_MANIFEST.json]
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = "/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python"
SCHEMA = "RAH_REPRO_MANIFEST/1"


def newest(pat):
    hits = sorted(glob.glob(os.path.join(ROOT, pat)))
    return hits[-1] if hits else None


def jload(p):
    fp = p if os.path.isabs(p) else os.path.join(ROOT, p)
    return json.load(open(fp)) if os.path.exists(fp) else None


# ---- readers: each pulls ONE headline number out of its raw artifact ---------------------- #
def r_phase1(cell, readout, field):
    d = jload("outputs/boombness/rah_phase1/rah_phase1_lift.json")
    return d["cells"][cell]["readouts"][readout][field]


def r_dose(cell, key, field):
    d = jload("outputs/boombness/rah_phase1b/rah_dose.json")
    return d["cells"][cell][key][field] if field else d["cells"][cell][key]


def r_screen(cell, field):
    d = jload("outputs/boombness/rah_screen/rah_screen_table.json")
    return [t for t in d["table"] if t["cell"] == cell][0][field]


def r_stagea(field):
    return jload("outputs/boombness/rah_stagea/rah_stagea_selection.json")["selected"][field]


def r_margin(field):
    return jload("outputs/boombness/rah_margin/rah_margin.json")[field]


def r_trackA_mass():
    d = newest("outputs/boombness/rah_transport/pr011_q_lp_*")
    rows = [json.loads(l) for l in open(os.path.join(d, "rows.jsonl")) if l.strip()]
    om = sorted(r["option_mass"] for r in rows if r["arm"] == "base")
    return om[len(om) // 2]


def r_preflight(f, form, R, field):
    d = jload(newest("outputs/boombness/rah_preflight/%s" % f))
    return [x for x in d["grid"] if x["form"] == form and x["R"] == R][0][field]


#: (id, description, reader, expected, tolerance)
NUMBERS = [
    ("RAH-R-004", "Qwen3 x lantern_poison, mapping-use arm count",
     lambda: r_phase1("Qwen3 x lantern_poison", "mapping_use", "counts")["natural_doublespeak"]["k"], 69, 0),
    ("RAH-R-004", "Qwen3 x lantern_poison, mapping-use BASE count (the no-mapping rate)",
     lambda: r_phase1("Qwen3 x lantern_poison", "mapping_use", "counts")["benign_literal"]["k"], 72, 0),
    ("RAH-R-004", "Qwen3 x lantern_poison, binding lift delta",
     lambda: r_phase1("Qwen3 x lantern_poison", "semantic", "delta_arm_minus_base"), 0.9375, 1e-9),
    ("RAH-R-004", "Llama x lantern_poison, mapping-use lift delta",
     lambda: r_phase1("Llama x lantern_poison", "mapping_use", "delta_arm_minus_base"), -0.1000, 1e-9),
    ("RAH-R-007", "Llama x candle_missile, n=16 attacks",
     lambda: r_dose("Llama-3.1-8B x candle_missile", "n16", "attacks"), 8, 0),
    ("RAH-R-007", "Llama x candle_missile, n=8 attacks",
     lambda: r_dose("Llama-3.1-8B x candle_missile", "n8", "attacks"), 7, 0),
    ("RAH-R-007", "Qwen3 x lantern_poison, n=16 ASR",
     lambda: r_dose("Qwen3-14B x lantern_poison", "n16", "asr"), 0.025, 1e-9),
    ("RAH-R-008", "Llama preflight, fc46 @ R=28 (the archived failing geometry)",
     lambda: r_preflight("rahpf_plp_*.json", "fc46", 28, "pos_ctrl_max"), 0.008784, 1e-5),
    ("RAH-R-008", "Llama preflight, fc_probe_last @ R=4 (the best config)",
     lambda: r_preflight("rahpf_plp_*.json", "fc_probe_last", 4, "pos_ctrl_max"), 0.8421, 1e-3),
    ("RAH-R-010", "Stage-A selection, min uplift across all six level-A runs",
     lambda: r_stagea("min_uplift_over_runs"), 0.8516, 1e-3),
    ("RAH-R-013", "equivalence margin (floored at the repo T3/T5 precedent)",
     lambda: r_margin("MARGIN"), 0.10, 1e-9),
    ("RAH-R-013", "nuisance-ensemble s_accuracy, worst model",
     lambda: r_margin("s_accuracy_p95_worst_model"), 0.075, 1e-6),
    ("RAH-R-018", "Track A held-out: median option mass on the base arm",
     r_trackA_mass, 7.147e-08, 1e-9),
    ("RAH-R-021", "Llama x carrot_bomb screening attacks",
     lambda: r_screen("Llama x carrot_bomb", "attacks"), 25, 0),
    ("RAH-R-021", "Llama x carrot_bomb screening ASR",
     lambda: r_screen("Llama x carrot_bomb", "baseline_asr"), 0.16447368421052633, 1e-9),
    ("RAH-R-021", "Qwen3 x carrot_bomb screening ASR (the discovery pair FAILS on Qwen3)",
     lambda: r_screen("Qwen3 x carrot_bomb", "baseline_asr"), 0.07236842105263158, 1e-9),
    ("RAH-R-021", "Qwen3 x ticket_knife k_informative (below the >=6 floor)",
     lambda: r_screen("Qwen3 x ticket_knife", "k_informative"), 3, 0),
]

#: independent verifiers -- programs that recompute an estimand WITHOUT importing its producer
VERIFIERS = [
    ("RAH-R-004", [PY, "scripts/rah_verify_phase1.py",
                   "--produced", "outputs/boombness/rah_phase1/rah_phase1_lift.json"]),
    ("RAH-R-007", [PY, "scripts/rah_verify_dose.py"]),
    ("RAH-R-010", [PY, "scripts/rah_select_config.py",
                   "--out", "/tmp/rah_repro_stagea.json"]),
    ("RAH-C-012", [PY, "scripts/rah_select_transport_config.py",
                   "--out", "/tmp/rah_repro_pr011.json"]),
    ("RAH-R-021", [PY, "scripts/rah_screen_table.py",
                   "--out", "/tmp/rah_repro_screen.json"]),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="reports/RAH_REPRO_MANIFEST.json")
    a = ap.parse_args()

    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                            text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True,
                           text=True).stdout.strip()

    print("REPRODUCTION MANIFEST -- executing, not listing")
    print("commit %s  dirty=%s\n" % (commit[:12], bool(dirty)))

    entries, failures = [], []
    print("%-12s %-62s %14s %14s  %s" % ("id", "number", "expected", "got", "result"))
    for cid, desc, reader, expected, tol in NUMBERS:
        try:
            got = reader()
            ok = (got == expected) if tol == 0 else (abs(float(got) - float(expected)) <= tol)
        except Exception as e:                                    # noqa: BLE001
            got, ok = "ERROR: %s" % e, False
        entries.append({"id": cid, "number": desc, "expected": expected, "got": got, "pass": ok})
        if not ok:
            failures.append("%s / %s: expected %r got %r" % (cid, desc, expected, got))
        print("%-12s %-62s %14s %14s  %s"
              % (cid, desc[:62], expected, got if not isinstance(got, float) else "%.6g" % got,
                 "PASS" if ok else "FAIL"))

    print("\nINDEPENDENT VERIFIERS (each recomputes without importing its producer)")
    vres = []
    for cid, cmd in VERIFIERS:
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        ok = r.returncode == 0
        vres.append({"id": cid, "cmd": " ".join(cmd[1:]), "returncode": r.returncode, "pass": ok})
        if not ok:
            failures.append("%s verifier exited %d" % (cid, r.returncode))
        print("  %-12s %-64s %s" % (cid, " ".join(cmd[1:])[:64], "PASS" if ok else
                                    "FAIL(rc=%d)" % r.returncode))

    out = {"schema": SCHEMA, "commit": commit, "tree_dirty": bool(dirty),
           "n_numbers": len(entries), "n_verifiers": len(vres),
           "numbers": entries, "verifiers": vres, "failures": failures,
           "EXECUTED": True, "PASS": not failures}
    os.makedirs(os.path.dirname(os.path.join(ROOT, a.out)), exist_ok=True)
    with open(os.path.join(ROOT, a.out), "w") as f:
        json.dump(out, f, indent=1)

    print("\n%d numbers, %d verifiers, %d failure(s)" % (len(entries), len(vres), len(failures)))
    for f_ in failures:
        print("   FAIL:", f_)
    print("-> %s" % a.out)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
