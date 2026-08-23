"""Stamp pre-gate comprehension artifacts with their own option-mass status.

WHY (2026-08-23). `g8_comprehension_DF_arms.json` and `g8_comprehension_by_nexamples.json` are computed
from runs whose median option mass is 3e-05 -- ~1000x below the `--min-option-mass 0.05` gate that
`score_behavior.py` itself calls fatal, and on the readout R-6 withdrew. The report marks them (audit
#16 retracted the DF table and replaced it with the GATEPASS recompute), but the ARTIFACTS carry
nothing: a reader who opens the JSON sees a clean-looking analysis and has no way to know.

A file should carry its own status rather than depend on the reader finding the right paragraph three
thousand lines into a report. That is the same "address things by identity" rule the sweep keeps
relearning, applied to artifacts instead of claims.

The mass is RECOMPUTED from the run dirs here, not asserted: these runs predate the `option_mass` field,
so it is reconstructed as p_coded+p_literal / p_codeword+p_concept.
"""
import glob
import json
import os
import statistics
import sys

GATE = 0.05
PAIR = {"comprehension_usage": ("p_coded", "p_literal"),
        "semantic_one_word": ("p_codeword", "p_concept"),
        "semantic_forced_choice": ("p_codeword", "p_concept")}
RUNS = "outputs/boombness/score_behavior"

# The gate applies to the readout an analysis USES, not to every readout its runs happen to contain.
# Both files below analyse `comprehension_logodds`, so `comprehension_usage` is the operative row set.
# This matters concretely: the DF successor's `semantic_one_word` is 0.0120 (sub-gate, inherited from
# wa_D), but it analyses comprehension at 0.3083 -- so the pointer is valid, and a naive
# all-readouts-must-pass check would have wrongly condemned the replacement.
TARGETS = {
    "outputs/boombness/g8_comprehension_DF_arms.json":
        ("outputs/boombness/g8_comprehension_DF_arms_GATEPASS.json", "comprehension_usage"),
    "outputs/boombness/g8_comprehension_by_nexamples.json":
        ("outputs/boombness/g8_comprehension_by_nexamples_GATEPASS.json", "comprehension_usage"),
}


def run_mass(run_dir):
    by = {}
    path = os.path.join(run_dir, "results.jsonl")
    if not os.path.exists(path):
        return {}
    with open(path) as fh:
        for line in fh:
            r = json.loads(line)
            k = r.get("query_kind")
            if k in PAIR:
                a, b = PAIR[k]
                if a in r and b in r:
                    by.setdefault(k, []).append(r[a] + r[b])
    return {k: statistics.median(v) for k, v in by.items()}


def main() -> int:
    all_runs = {os.path.basename(d.rstrip("/")): d
                for d in glob.glob(os.path.join(RUNS, "*/"))}
    changed = 0
    for path, (successor, readout) in TARGETS.items():
        if not os.path.exists(path):
            print(f"[stamp] missing {path}", file=sys.stderr)
            return 2
        text = open(path).read()
        d = json.loads(text)
        cited = sorted(n for n in all_runs if n in text)
        if not cited:
            print(f"[stamp] REFUSING: {path} names no run dir -- cannot verify its mass",
                  file=sys.stderr)
            return 2
        masses = {}
        for n in cited:
            for k, m in run_mass(all_runs[n]).items():
                masses.setdefault(k, []).append(m)
        worst = {k: min(v) for k, v in masses.items()}
        if not worst:
            print(f"[stamp] REFUSING: no readout rows found for {path}", file=sys.stderr)
            return 2
        # VERIFY the successor before pointing at it: a stamp that redirects a reader to another
        # sub-gate file is worse than no stamp.
        succ_text = open(successor).read()
        succ_runs = sorted(n for n in all_runs if n in succ_text)
        succ_mass = {}
        for n in succ_runs:
            m = run_mass(all_runs[n]).get(readout)
            if m is not None:
                succ_mass[n] = m
        if not succ_mass or min(succ_mass.values()) < GATE:
            print(f"[stamp] REFUSING: successor {successor} does not clear the gate on {readout} "
                  f"({succ_mass}) -- do not redirect a reader to it", file=sys.stderr)
            return 2
        sub = {k: v for k, v in worst.items() if v < GATE}
        if not sub:
            print(f"[stamp] {os.path.basename(path)}: all readouts clear the gate -- not stamping")
            continue
        d["_OPTION_MASS_SUBGATE"] = {
            "gate": GATE,
            "worst_median_option_mass_by_readout": worst,
            "runs_checked": cited,
            "note": ("These medians are ~1000x below the --min-option-mass gate score_behavior.py "
                     "calls fatal, on the readout R-6 withdrew. Every verdict in this file is an "
                     "ordering inside that tail."),
            "readout_used_by_this_analysis": readout,
            "superseded_by": successor,
            "successor_verified": {"readout": readout,
                                   "worst_median_option_mass": min(succ_mass.values()),
                                   "runs": sorted(succ_mass)},
            "recomputed_by": "src/boombness/stamp_subgate_artifacts.py",
        }
        json.dump(d, open(path, "w"), indent=1)
        changed += 1
        print(f"[stamp] {os.path.basename(path)}: SUB-GATE "
              + ", ".join(f"{k}={v:.2e}" for k, v in sorted(sub.items()))
              + f"  -> superseded_by {os.path.basename(successor)}")
    print(f"[stamp] {changed} artifact(s) stamped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
