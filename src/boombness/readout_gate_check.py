"""readout_gate_check.py — which artifacts rest on a readout the gate says is NOT REPORTABLE?

THE DEFECT CLASS. `score_behavior.py` sets `--min-option-mass 0.05` and calls falling below it FATAL:
a forced choice decided inside a 1e-5 tail is not a forced choice, and such a run is marked "NOT
reportable as a comprehension or semantic result". Retraction R-6 withdrew one such readout.

On 2026-08-23 I published two sections computed on runs whose median option mass is **4.4e-05** --
about 1000x below that gate -- and the report stated the objection five paragraphs above one of the
tables. Gate-passing counterparts were on disk, unused. Recomputing on them REVERSED the headline's
sign. That is the worst error of this sprint, and it was mechanically detectable from the runs' own
`summary.json`.

WHY A SCANNER. The two guards that could have caught it were tied to specific figures and specific
artifacts. This is tied to the DATA, like `empty_goal_leakage_check`: for every committed artifact it
resolves the score_behavior runs behind it and asks what the gate says.

THREE STATES, and the middle one is the trap:
  PASS        the run recorded `option_mass_gate: PASS`.
  OVERRIDDEN  the run recorded "OVERRIDDEN -- NOT REPORTABLE". Loud, and easy to respect.
  ABSENT      no gate field at all (the run predates it). SILENT, and this is where the failure lived.
              For these the option mass is COMPUTED here from p_coded/p_literal rather than assumed.

KNOWN IMPRECISION, stated because it bit on first use. `OVERRIDDEN` is recorded PER READOUT --
"OVERRIDDEN ... semantic/semantic_one_word: median option mass 0.01205" says the *semantic* readout is
unreportable and says nothing about *comprehension*. This check treats the flag as blanket, so it
over-reports: it flagged the corrected `g8_comprehension_DF_arms_GATEPASS.json`, whose three runs all
have `comprehension_usage` median mass **0.31-0.33**, an order of magnitude ABOVE the gate. That
artifact is fine. Until the flag is parsed per readout, treat an `OVERRIDDEN` hit as "go and check
which readout", not as a verdict -- and a `PASS`/`ABSENT_SUB_GATE` hit as the real signal.

The complementary limitation, shared with `empty_goal_leakage_check`: "named in a deliverable" cannot
yet distinguish *quoted as evidence* from *named inside its own retraction notice*, so retracted
artifacts keep showing as LIVE after they are correctly withdrawn.

Reads numeric fields only.
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from unanalysed_inventory import git_commit_safe  # noqa: E402

MIN_OPTION_MASS = 0.05          # the value score_behavior.py enforces
DELIVERABLES = ("reports/boombness_objective_sprint_report.md",
                "reports/boombness_objective_sprint_short_update.md")

#: Scripts whose output DEPENDS on the forced-choice readout (p_coded / p_literal). The gate only
#: bears on these; an artifact that merely NAMES a run -- an index, a drift estimate, an ASR
#: decomposition -- is unaffected by how much option mass that run had.
#:
#: IDENTIFIED BY PRODUCING SCRIPT, not by keyword. The first version of this check matched artifact
#: text for "comprehension"/"semantic" and got it backwards both ways: g8_comprehension_by_nexamples
#: -- which is entirely a forced-choice readout -- contains neither word (its keys are `curve`,
#: `arms`, condition names), while replicate_noise -- which uses ASR only -- contains both, inside
#: `query_kinds` strings. That is address-by-incidental-property, which this repo has been bitten by
#: repeatedly. The producing script is the identity.
READOUT_SCRIPTS = ("analyze_g8.py", "analyze_g2.py", "analyze_g9.py", "analyze_position.py",
                   "summarize_section8.py", "summarize_section9.py")


def option_mass(run_dir):
    """Median p_coded+p_literal over rows that have both. None if the readout is absent."""
    f = os.path.join(run_dir, "results.jsonl")
    if not os.path.exists(f):
        return None, 0
    ms = []
    for line in open(f, encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        pc, pl = r.get("p_coded"), r.get("p_literal")
        if pc is not None and pl is not None:
            ms.append(pc + pl)
    return (statistics.median(ms) if ms else None), len(ms)


def classify(run_dir):
    s = os.path.join(run_dir, "summary.json")
    gate = None
    if os.path.exists(s):
        try:
            gate = json.load(open(s)).get("option_mass_gate")
        except Exception:
            pass
    if isinstance(gate, str) and gate.startswith("OVERRIDDEN"):
        return "OVERRIDDEN", gate, None
    if gate == "PASS":
        return "PASS", gate, None
    med, n = option_mass(run_dir)
    if med is None:
        return "NO_READOUT", gate, None      # no forced-choice readout: the gate does not apply
    return ("ABSENT_SUB_GATE" if med < MIN_OPTION_MASS else "ABSENT_OK"), gate, med


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    runs = {}
    for d in sorted(glob.glob("outputs/boombness/score_behavior/*")):
        if os.path.isdir(d):
            st, gate, med = classify(d)
            runs[os.path.basename(d)] = {"state": st, "gate": gate, "median_option_mass": med}

    bad = {k for k, v in runs.items() if v["state"] in ("OVERRIDDEN", "ABSENT_SUB_GATE")}

    text = ""
    for p in DELIVERABLES:
        try:
            text += io.open(p, encoding="utf-8").read()
        except OSError:
            pass

    flagged, skipped = [], []
    for p in sorted(glob.glob("outputs/boombness/*.json")):
        b = os.path.basename(p)
        try:
            blob = open(p, encoding="utf-8").read()
            doc = json.loads(blob)
        except Exception:
            continue
        cited = sorted(r for r in bad if r in blob)
        if not cited:
            continue
        argv = ((doc.get("provenance") or {}).get("argv") or []) if isinstance(doc, dict) else []
        producer = os.path.basename(argv[0]) if argv else None
        # NO PROVENANCE IS NOT EVIDENCE OF SAFETY. The g8 artifacts -- the exact case this check was
        # written for -- carry no `provenance` key at all, so keying only on argv silently skipped
        # them: the check exonerated the artifacts that motivated it. Fall back to the artifact's own
        # name, and when neither identifies a producer, FLAG rather than skip, because "unknown" must
        # not read as "fine".
        if producer is None:
            stem = b.replace(".json", "")
            for s in READOUT_SCRIPTS:
                fam = s.replace("analyze_", "").replace("summarize_section", "g").replace(".py", "")
                if stem.startswith(fam) or stem.startswith(fam.replace("g", "g") + "_"):
                    producer = s
                    break
        if producer is None:
            producer = "UNKNOWN (no provenance, name unmatched) -- flagged, not skipped"
        elif producer not in READOUT_SCRIPTS:
            skipped.append({"artifact": b, "producer": producer,
                            "why": "names a sub-gate run but its output does not depend on the "
                                   "forced-choice readout"})
            continue
        flagged.append({
            "artifact": b,
            "sub_gate_runs_cited": cited,
            "worst_median_option_mass": min(
                (runs[r]["median_option_mass"] for r in cited
                 if runs[r]["median_option_mass"] is not None), default=None),
            "artifact_named_in_a_deliverable": (b in text or b.replace(".json", "") in text),
        })

    live = [f for f in flagged if f["artifact_named_in_a_deliverable"]]
    counts = {}
    for v in runs.values():
        counts[v["state"]] = counts.get(v["state"], 0) + 1

    out = {
        "question": "which artifacts rest on a forced-choice readout the gate calls NOT REPORTABLE?",
        "gate": {"min_option_mass": MIN_OPTION_MASS,
                 "source": "score_behavior.py, which calls falling below this FATAL"},
        "three_states": {
            "PASS": "run recorded option_mass_gate: PASS",
            "OVERRIDDEN": "run recorded 'OVERRIDDEN -- NOT REPORTABLE'; loud and easy to respect",
            "ABSENT": "no gate field (run predates it) -- SILENT, and where the 2026-08-23 failure "
                      "lived. Option mass is COMPUTED here, not assumed.",
        },
        "run_state_counts": counts,
        "n_runs_not_reportable": len(bad),
        "n_artifacts_resting_on_them": len(flagged),
        "artifacts": flagged,
        "readout_scripts": list(READOUT_SCRIPTS),
        "named_a_sub_gate_run_but_gate_does_not_apply": skipped,
        "LIVE_in_a_deliverable": live,
        "runs": runs,
        "provenance": {"argv": sys.argv, "git_commit": git_commit_safe()},
    }
    with open(a.out, "w") as f:
        json.dump(out, f, indent=2)

    print("run states:", counts)
    print(f"runs NOT reportable (overridden or sub-gate): {len(bad)}")
    print(f"artifacts whose READOUT rests on them: {len(flagged)}  "
          f"(+{len(skipped)} merely name one; gate does not apply)\n")
    for f_ in flagged:
        mark = "LIVE IN DELIVERABLE" if f_["artifact_named_in_a_deliverable"] else "not quoted"
        mm = f_["worst_median_option_mass"]
        print(f"   {f_['artifact'][:44]:46s} {len(f_['sub_gate_runs_cited'])} run(s)  "
              f"worst mass={mm if mm is None else f'{mm:.2e}'}  [{mark}]")
    print(f"\n*** LIVE: {len(live)} ***")
    print(f"\n[readout-gate] -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
